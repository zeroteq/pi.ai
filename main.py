from fastapi import FastAPI
import aiohttp
from pydantic import BaseModel

app = FastAPI()

PI_AI_URL = "https://pi.ai/api/chat"

HEADERS = {
    "accept": "application/json",
    "x-api-version": "3"
}

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None

async def start_conversation():
    """Starts a new conversation and returns conversation ID."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{PI_AI_URL}/start", json={}, headers=HEADERS) as response:
            if response.status == 200:
                data = await response.json()
                return data["conversations"][0]["sid"]
            return None

async def send_message(conversation_id, message):
    """Sends a message and gets response from Pi.ai."""
    payload = {
        "text": message,
        "conversation": conversation_id,
        "mode": "BASE",
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{PI_AI_URL}", json=payload, headers=HEADERS) as response:
            if response.status == 200:
                data = await response.json()
                return data
            return None

@app.post("/chat")
async def chat(request: ChatRequest):
    if not request.conversation_id:
        request.conversation_id = await start_conversation()
        if not request.conversation_id:
            return {"error": "Failed to start conversation."}
    
    response = await send_message(request.conversation_id, request.message)
    return {"conversation_id": request.conversation_id, "response": response}
