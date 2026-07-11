import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from app.providers.ollama_provider import OllamaProvider

async def main() -> None:
    provider = OllamaProvider()
    try:
        result = await provider.generate([{"role": "user", "content": "Merhaba"}], model="qwen2.5:3b")
        print(result)
    except Exception as exc:
        import traceback
        traceback.print_exc()

asyncio.run(main())
