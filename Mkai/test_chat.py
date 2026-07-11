import httpx
import asyncio

async def test():
    url = 'http://127.0.0.1:8000/api/v1/chat'
    payload = {'message': 'merhaba', 'conversation_id': None}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        print(f'Status: {resp.status_code}')
        data = resp.json()
        if resp.status_code == 200:
            print(f'Reply: {data.get("reply", "")[:200]}')
        else:
            print(f'Error: {data.get("detail", str(data))[:300]}')

asyncio.run(test())
