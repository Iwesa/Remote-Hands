import asyncio
import json
import base64
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types

from agent import run_research_agent

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Initialize the Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# THE GEMINI TOOL DECLARATION
manual_search_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_technical_manuals",
            description="Searches the live internet, surveying forums, and digital manuals for specific equipment troubleshooting steps.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "The specific error code or equipment issue."
                    }
                },
                "required": ["query"]
            }
        )
    ]
)

# WEBSOCKET ROUTING & LIVE API
async def receive_from_frontend(websocket: WebSocket, session):
    """Receives audio and video frames from the phone and streams them to Gemini."""
    try:
        while True:
            message_str = await websocket.receive_text()
            message = json.loads(message_str)
            
            if message.get("type") == "audio":
                audio_data = base64.b64decode(message.get("data"))
                if not audio_data: continue 
                await session.send_realtime_input(
                    media=types.Blob(data=audio_data, mime_type="audio/pcm;rate=16000")
                )
                
            elif message.get("type") == "video":
                image_data = base64.b64decode(message.get("data"))
                if not image_data: continue
                await session.send_realtime_input(
                    media=types.Blob(data=image_data, mime_type="image/jpeg")
                )
    except WebSocketDisconnect:
        print("Frontend disconnected normally.")
    except Exception as e:
        print(f"Frontend Stream Error: {e}")

async def receive_from_gemini(websocket: WebSocket, session):
    """Receives audio/text from Gemini, intercepts tool calls, and sends data to the phone."""
    try:
        while True: 
            async for response in session.receive():
                
                # INTERCEPT TOOL CALLS HERE
                if response.tool_call:
                    for fc in response.tool_call.function_calls:
                        args = dict(fc.args) if fc.args else {}
                        query = args.get("query", "equipment issue")
                        try: await websocket.send_json({"type": "status", "data": f"Searching manuals for: {query}..."})
                        except: pass
                        
                        # Call the external LangGraph agent
                        result = await run_research_agent(query)
                        
                        # Send the web research back to Gemini
                        await session.send_tool_response(
                            function_responses=[
                                types.FunctionResponse(id=fc.id, name=fc.name, response={"result": result})
                            ]
                        )

                server_content = response.server_content
                if server_content is not None:
                    model_turn = server_content.model_turn
                    if model_turn is not None:
                        for part in model_turn.parts:
                            if part.text:
                                await websocket.send_json({"type": "text", "data": part.text})
                            if part.inline_data:
                                audio_base64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                                await websocket.send_json({"type": "audio", "data": audio_base64})
                            try: await websocket.send_json({"type": "status", "data": "Agent Listening..."})
                            except: pass

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Gemini API Error: {e}")
        try: await websocket.send_json({"type": "status", "data": "API Connection Lost"})
        except: pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("--- New Field Session Started ---")
    
    send_task = None
    receive_task = None
    
    try:
        async with client.aio.live.connect(
            model="gemini-2.5-flash-native-audio-preview-12-2025", 
            config={
                "tools": [manual_search_tool],
                "response_modalities": ["AUDIO"], 
                "system_instruction": types.Content(
                    parts=[types.Part.from_text(
                        text="You are an expert technical assistant. You help field crews troubleshoot high-precision equipment. ALWAYS use the tool if the user asks about a specific error. Keep answers concise, practical, and conversational."
                    )]
                )
            }
        ) as session:
            
            await asyncio.sleep(0.5)
            await session.send(
                input="Hello! I just connected. Please introduce yourself out loud and tell me you are ready to troubleshoot my equipment.",
                end_of_turn=True
            )

            send_task = asyncio.create_task(receive_from_frontend(websocket, session))
            receive_task = asyncio.create_task(receive_from_gemini(websocket, session))
            
            # Wait for either task to finish (usually the user hitting End Session)
            await asyncio.wait(
                [send_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

    except Exception as e:
        print(f"Session System Error: {e}")
        try: await websocket.send_json({"type": "status", "data": "Server Disconnected"})
        except: pass
    finally:
        # Aggressive Cleanup
        for task in [send_task, receive_task]:
            if task and not task.done():
                task.cancel()
        try: await websocket.close()
        except: pass
        print("--- Session Safely Terminated ---")

# CLOUD RUN PORT BINDING
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)