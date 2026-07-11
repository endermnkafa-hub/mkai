import sys
sys.path.insert(0, 'backend')

import asyncio
from app.core.config import settings
from app.providers.router import router

async def test():
    messages = [
        {"role": "user", "content": "test"}
    ]
    
    try:
        result = await router.generate(messages)
        print(f"Router result: {result.get('text', '')[:200]}")
    except Exception as e:
        import traceback
        print(f"Router error: {type(e).__name__}: {e}")
        traceback.print_exc()

asyncio.run(test())
