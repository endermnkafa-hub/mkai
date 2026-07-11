import sys
sys.path.insert(0, 'backend')

import asyncio
from app.schemas.chat import ChatRequest
from app.services.assistant_service import AssistantService

async def test():
    assistant = AssistantService()
    request = ChatRequest(message='test', conversation_id=None)
    
    try:
        result = await assistant.generate_reply(request, history=[])
        print(f"Success: {result.reply[:200]}")
        print(f"Model: {result.model}")
    except Exception as e:
        import traceback
        print(f"Error: {type(e).__name__}: {e}")
        traceback.print_exc()

asyncio.run(test())
