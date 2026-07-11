import httpx
import asyncio

async def check():
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get('http://127.0.0.1:11434/api/tags')
        print(f'Ollama tags: {resp.status_code}')
        if resp.status_code == 200:
            import json
            data = resp.json()
            models = [m['name'] for m in data.get('models', [])]
            print(f'Models: {models}')

asyncio.run(check())
