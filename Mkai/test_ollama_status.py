import httpx
import asyncio

async def test():
    # Test tags
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get('http://127.0.0.1:11434/api/tags')
            print(f"Tags: {resp.status_code}")
            if resp.status_code == 200:
                print(resp.json())
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test chat
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            payload = {
                "model": "qwen2.5:3b",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False,
            }
            resp = await client.post('http://127.0.0.1:11434/api/chat', json=payload)
            print(f"\nChat (qwen2.5:3b): {resp.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test with llama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            payload = {
                "model": "llama3.2:3b",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False,
            }
            resp = await client.post('http://127.0.0.1:11434/api/chat', json=payload)
            print(f"Chat (llama3.2:3b): {resp.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

asyncio.run(test())
