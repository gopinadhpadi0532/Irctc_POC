from fastapi import FastAPI
from pydantic import BaseModel
from app.services import llm_chat

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str
    provider: str = "groq"


@app.post("/llm_chat")
async def llm_chat_endpoint(req: ChatRequest):
    resp = llm_chat(req.prompt, provider=req.provider)
    return {"text": resp.get("text"), "raw": resp.get("raw")}
