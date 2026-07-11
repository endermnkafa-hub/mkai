import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get('http://127.0.0.1:11434/api/tags')
        print(response.status_code)
        print(response.text)

asyncio.run(main())
