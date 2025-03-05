from requests.cookies import RequestsCookieJar
import json
from ..typing import AsyncResult, Messages, Cookies
from .base_provider import AsyncGeneratorProvider, format_prompt
from ..requests import StreamSession, get_args_from_nodriver, raise_for_status, merge_cookies

class Pi(AsyncGeneratorProvider):
    url = "https://pi.ai/talk"
    working = True
    use_nodriver = True
    supports_stream = True
    default_model = "pi"
    models = [default_model]
    _headers: dict = None
    _cookies: Cookies = {}

    @classmethod
    async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        stream: bool,
        proxy: str = None,
        timeout: int = 180,
        conversation_id: str = None,
        **kwargs
    ) -> AsyncResult:
        if cls._headers is None:
            args = await get_args_from_nodriver(cls.url, proxy=proxy, timeout=timeout)
            cls._cookies = args.get("cookies", {})
            cls._headers = args.get("headers")
        
        # Handle cookies properly
        cookies = RequestsCookieJar()
        for cookie_name, cookie_value in cls._cookies.items():
            cookies.set(cookie_name, cookie_value)

        headers = {
            'accept': 'application/json',
            'x-api-version': '3',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        async with StreamSession(headers=headers, cookies=cookies, proxy=proxy) as session:
            if not conversation_id:
                conversation_id = await cls.start_conversation(session)
                prompt = format_prompt(messages)
            else:
                prompt = messages[-1]["content"]
            answer = cls.ask(session, prompt, conversation_id)
            async for line in answer:
                if "text" in line:
                    yield line["text"]        

    @classmethod
    async def start_conversation(cls, session: StreamSession) -> str:
        headers = {
            'accept': 'application/json',
            'x-api-version': '3',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Ensure cookies are passed in the request
        cookies = RequestsCookieJar()
        for cookie_name, cookie_value in cls._cookies.items():
            cookies.set(cookie_name, cookie_value)

        async with session.post('https://pi.ai/api/chat/start', data="{}", headers=headers, cookies=cookies) as response:
            await raise_for_status(response)
            return (await response.json())['conversations'][0]['sid']
        
    async def get_chat_history(session: StreamSession, conversation_id: str):
        params = {
            'conversation': conversation_id,
        }
        async with session.get('https://pi.ai/api/chat/history', params=params) as response:
            await raise_for_status(response)
            return await response.json()

    @classmethod
    async def ask(cls, session: StreamSession, prompt: str, conversation_id: str):
        json_data = {
            'text': prompt,
            'conversation': conversation_id,
            'mode': 'BASE',
        }

        # Ensure cookies are passed in the request
        cookies = RequestsCookieJar()
        for cookie_name, cookie_value in cls._cookies.items():
            cookies.set(cookie_name, cookie_value)

        async with session.post('https://pi.ai/api/chat', json=json_data, cookies=cookies) as response:
            await raise_for_status(response)
            cls._cookies = merge_cookies(cls._cookies, response)
            async for line in response.iter_lines():
                if line.startswith(b'data: {"text":'):
                    yield json.loads(line.split(b'data: ')[1])
                elif line.startswith(b'data: {"title":'):
                    yield json.loads(line.split(b'data: ')[1])
