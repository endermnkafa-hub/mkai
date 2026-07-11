import httpx
import asyncio

async def test():
    for i in range(3):
        payload = {
            "model": "qwen2.5:3b",
            "messages": [
                {"role": "user", "content": f"test {i}"}
            ],
            "stream": False,
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post('http://127.0.0.1:11434/api/chat', json=payload)
                print(f"Request {i}: {resp.status_code}")
        except Exception as e:
            print(f"Request {i}: Error - {e}")

asyncio.run(test())
