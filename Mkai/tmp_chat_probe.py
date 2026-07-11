import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from app.api.v1.endpoints.chat import _handle_chat
from app.schemas.chat import ChatRequest

async def main() -> None:
    request = ChatRequest(message='Merhaba', user_id='muhammed', workspace='Naruto Mod')
    response = await _handle_chat(request, db=None)
    print(response)

asyncio.run(main())
