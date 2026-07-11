import httpx
import asyncio
import json

async def test():
    payload = {
        "message": "merhaba",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post('http://127.0.0.1:8000/api/v1/chat', json=payload)
            print(f"Status: {resp.status_code}")
            print(f"Headers: {dict(resp.headers)}")
            print(f"Body:\n{resp.text}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
