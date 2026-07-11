import httpx
import asyncio
import traceback
import sys

async def test_provider():
    # Import provider with detailed logging
    sys.path.insert(0, 'backend')
    from app.core.config import settings
    from app.providers.ollama_provider import OllamaProvider

    provider = OllamaProvider()
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'test'}
    ]
    
    print(f"Settings ollama_base_url: {settings.ollama_base_url}")
    print(f"Settings ollama_model: {settings.ollama_model}")
    print(f"Messages: {messages}")
    
    try:
        result = await provider.generate(messages)
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_provider())
