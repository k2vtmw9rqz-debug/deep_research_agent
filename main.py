from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import os, httpx
from datetime import datetime

app = FastAPI(title="deep_research_agent", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SYSTEM_PROMPT = "You are a professional research agent specializing in comprehensive topic analysis. Your role is to:\n\n1. Break down complex research topics into manageable sub-questions\n2. Conduct thorough searches across multiple reliable sources\n3. Extract and synthesize information while maintaining accuracy\n4. Provide proper citations for all claims and data\n5. Present findings in a well-structured, academic format\n\nAlways prioritize:\n- Source credibility and authority\n- Factual accuracy and verification\n- Comprehensive coverage of the topic\n- Clear, logical organization\n- Proper citation format (APA style)\n\nWhen uncertain about information, explicitly state limitations and suggest areas for further research."
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

@app.get("/")
def index():
    with open("index.html") as f:
        return HTMLResponse(f.read())

@app.get("/info")
def info():
    return {"agent": "deep_research_agent", "description": "An AI research agent that conducts comprehensive topic analysis with proper citations and source verification"}

@app.post("/chat")
async def chat(req: ChatRequest):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(500, "ANTHROPIC_API_KEY not set")
    conv_id = req.conversation_id or datetime.now().strftime("%Y%m%d%H%M%S%f")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "system": SYSTEM_PROMPT, "messages": [{"role": "user", "content": req.message}]},
            timeout=60.0,
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, "AI API error")
    data = resp.json()
    text = "".join(c.get("text", "") for c in data.get("content", []))
    return {"response": text, "conversation_id": conv_id, "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))