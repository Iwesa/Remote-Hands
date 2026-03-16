import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun

def get_search_agent():
    """Initializes and returns the LangGraph ReAct agent armed with web search."""
    # Initialize the live internet search tool
    internet_search = DuckDuckGoSearchRun(
        name="search_technical_manuals",
        description="Searches the live internet, surveying forums, and digital manuals for specific equipment troubleshooting steps."
    )

    # Initialize the reasoning LLM 
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

    # Build and return the agent
    return create_react_agent(llm, tools=[internet_search])

async def run_research_agent(query: str) -> str:
    """The main entry point to be called from your WebSocket server."""
    print(f"LangGraph researching live web for: {query}")
    try:
        agent = get_search_agent()
        
        # Invoke the agent asynchronously
        result = await agent.ainvoke(
            {"messages": [("user", f"You are an expert land surveying technical assistant. Search the web to find real, specific troubleshooting steps for: {query}. Keep the final answer concise, practical, and conversational so it can be spoken out loud to a field crew.")]}
        )
        
        final_answer = result["messages"][-1].content
        print(f"LangGraph Web Output: {final_answer}")
        return final_answer
        
    except Exception as e:
        print(f"LangGraph Error: {str(e)}")
        return "I'm sorry, I couldn't reach the manual database right now. Please check standard calibration procedures."