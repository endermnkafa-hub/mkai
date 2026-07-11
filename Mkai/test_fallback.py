import httpx
import asyncio

async def test():
    fallback_payload = {
        "model": "qwen2.5:3b",
        "prompt": "System prompt line 1\nSystem prompt line 2\nUser message text",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.95,
            "num_predict": 600,
        },
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post('http://127.0.0.1:11434/api/generate', json=fallback_payload)
        print(f'Status: {resp.status_code}')
        if resp.status_code != 200:
            print(f'Error: {resp.text[:300]}')
        else:
            data = resp.json()
            print(f'Response: {data.get("response", "")[:200]}')

asyncio.run(test())
