import sys
sys.path.insert(0, 'backend')

import asyncio
from app.services.prompt_builder import PromptBuilder
from app.providers.ollama_provider import OllamaProvider

async def test():
    prompt_builder = PromptBuilder()
    messages = prompt_builder.build_messages('test', history=[], user_language='en')
    
    print(f"Messages: {len(messages)}")
    for msg in messages:
        print(f"  - {msg.get('role')}: {msg.get('content', '')[:100]}")
    
    provider = OllamaProvider()
    try:
        result = await provider.generate(messages)
        print(f"SUCCESS: {result}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        
        # Trysimpler version without system message
        print("\nRetrying with just user message...")
        simple_messages = [{"role": "user", "content": "test"}]
        try:
            result = await provider.generate(simple_messages)
            print(f"SUCCESS (simple): {result}")
        except Exception as e2:
            print(f"ERROR (simple): {type(e2).__name__}: {e2}")

asyncio.run(test())
