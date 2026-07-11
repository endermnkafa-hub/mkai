import asyncio
import os
import sys

os.chdir(r'C:\Users\muhammed kılıç\OneDrive\Desktop\Mkai\backend')
sys.path.insert(0, os.getcwd())

from app.providers.router import router


async def main() -> None:
    result = await router.generate([{'role': 'user', 'content': 'Merhaba'}], provider='ollama')
    print(result)


asyncio.run(main())
