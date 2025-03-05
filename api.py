from fastapi import FastAPI
import asyncio
import json
from aiohttp import ClientSession

app = FastAPI()

class PiAI:
    BASE_URL = "https://pi.ai"

    @staticmethod
    async def start_conversation(session: ClientSession):
        async with session.post(f"{PiAI.BASE_URL}/api/chat/start", json={}) as response:
            data = await response.json()
            return data['conversations'][0]['sid']

    @staticmethod
    async def ask_question(prompt: str, conversation_id: str = None):
        async with ClientSession() as session:
            if not conversation_id:
                conversation_id = await PiAI.start_conversation(session)

            json_data = {
                "text": prompt,
                "conversation": conversation_id,
                "mode": "BASE",
            }

            async with session.post(f"{PiAI.BASE_URL}/api/chat", json=json_data) as response:
                async for line in response.content:
                    try:
                        data = json.loads(line.decode().strip().split("data: ")[1])
                        if "text" in data:
                            return data["text"]
                    except:
                        continue

@app.get("/chat")
async def chat(prompt: str, conversation_id: str = None):
    response = await PiAI.ask_question(prompt, conversation_id)
    return {"response": response}
