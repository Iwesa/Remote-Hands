# The Remote-Hands
## Your AI-Powered Multimodal Surveying Assistant
The Remote Hands is a real-time, hands-free technical assistant designed for land surveyors. It leverages the Gemini 3 Flash Live API to provide visual recognition and voice-activated troubleshooting in the field.
## Keya Features
**Multimodal Vision:** Point your phone camera at surveying gear (Total Stations, GPS Rovers, Theodolites). The agent identifies the equipment and understands the physical context.
**Real-Time Voice Link:** Ultra-low latency, bi-directional audio allows for natural conversation while your hands are busy leveling tribrachs or adjusting antennas.
**LangGraph-Powered Research:** When a specific error code appears, the assistant triggers a **ReAct Agent** that scrapes the live web and technical forums to find the exact manufacturer protocol.
**Field Ready:** Optimized for mobile browser performance and deployed on **Google Cloud Run** for high availability.
## The Tech Stack
- **Core AI:** Gemini 3 Flash (Live API) & Gemini 2.0 Flash (Reasoning).
- **Agentic Framework:** LangGraph for autonomous web-research cycles.
- **Backend:** FastAPI with high-performance WebSockets.
- **Cloud:** Google Cloud Run (Containerized with Docker).
- **Frontend:** Mobile-first HTML5/JavaScript with raw PCM audio processing.
## Technical Architecture
The system operates as a "double-loop" agentic workflow:
1. **The Live Loop:** Streams JPEG frames and PCM audio between the surveyor's phone and the Gemini Live API.
2. **The Research Loop:** If a technical query is detected, Gemini calls a tool that invokes a **LangGraph ReAct Agent**. This agent utilizes **DuckDuckGo Search** to browse the web, synthesizes the findings, and returns the answer to the Live Loop.
## Getting Started
**Prerequisites**
- A Google AI Studio API Key.
- Python 3.10+.
- Google Cloud SDK (for deployment).
**Local Setup**
1. **Clone the repo:**
    git clone https://github.com/IWesa/Remote-Hands.git
    cd remote-hands-agent
2. **Install dependancies:**
    pip install -r requirements.txt
3. **Run the server:**
    export GEMINI_API_KEY="your_key_here"
    export GOOGLE_API_KEY="your_key_here"
    python main.py
## Project Vision
Surveying equipment is becoming increasingly complex. The Remote Hands aims to bridge the gap between sophisticated hardware and on-site human expertise, ensuring that no project is delayed due to a missing manual or a cryptic error code.
