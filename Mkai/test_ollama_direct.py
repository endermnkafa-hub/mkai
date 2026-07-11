import httpx
import asyncio

async def test():
    # Test both endpoints with exact same payload
    payload = {
        "model": "qwen2.5:3b",
        "messages": [
            {"role": "user", "content": "test"}
        ],
        "stream": False,
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Test /api/chat
        print("Testing /api/chat...")
        try:
            resp = await client.post('http://127.0.0.1:11434/api/chat', json=payload)
            print(f"  Status: {resp.status_code}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Test /api/generate with prompt
        payload2 = {
            "model": "qwen2.5:3b",
            "prompt": "test",
            "stream": False,
        }
        print("Testing /api/generate...")
        try:
            resp = await client.post('http://127.0.0.1:11434/api/generate', json=payload2)
            print(f"  Status: {resp.status_code}")
        except Exception as e:
            print(f"  Error: {e}")

asyncio.run(test())
