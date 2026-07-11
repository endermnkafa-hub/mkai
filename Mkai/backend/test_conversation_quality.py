"""E2E test for Conversation Quality Overhaul."""
import asyncio
import httpx
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
USER_ID = "test_quality_user_1"

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def chat(message: str, history: list = None) -> str:
    payload = {
        "message": message,
        "user_id": USER_ID,
        "history": history or [],
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(f"{BASE_URL}/chat", json=payload)
        resp.raise_for_status()
        return resp.json()["reply"]

async def main():
    print("=" * 60)
    print("MKAI CONVERSATION QUALITY TEST")
    print("=" * 60)

    history = []

    # Test 1: Selamlaşma
    msg1 = "Selamın aleyküm"
    print(f"\nKULLANICI: {msg1}")
    r1 = await chat(msg1)
    print(f"MKAI: {r1}")
    history.append({"role": "user", "content": msg1})
    history.append({"role": "assistant", "content": r1})

    # Test 2: Hafıza Kaydetme & Doğal Kullanım
    msg2 = "En sevdiğim renk siyah."
    print(f"\nKULLANICI: {msg2}")
    r2 = await chat(msg2, history)
    print(f"MKAI: {r2}")
    history.append({"role": "user", "content": msg2})
    history.append({"role": "assistant", "content": r2})

    # Hafıza Sorusu
    msg3 = "En sevdiğim renk ne?"
    print(f"\nKULLANICI: {msg3}")
    r3 = await chat(msg3, history)
    print(f"MKAI: {r3}")
    history.append({"role": "user", "content": msg3})
    history.append({"role": "assistant", "content": r3})

    # Test 3: Big Bang'i Anlatma (Öğretmen gibi analoji)
    msg4 = "Big Bang'i 10 yaşındaki bir çocuğa anlat."
    print(f"\nKULLANICI: {msg4}")
    r4 = await chat(msg4, history)
    print(f"MKAI: {r4}")

    # Test 4: Kod Talebi (Python ile Flappy Bird)
    msg5 = "Bana Python ile Flappy Bird yaz."
    print(f"\nKULLANICI: {msg5}")
    r5 = await chat(msg5, history)
    print(f"MKAI (İlk 300 karakter): {r5[:300]}...")

    print("\n" + "=" * 60)
    print("DEĞERLENDİRME:")
    print(f"1. Selamlaşma Yanıtı: {r1}")
    print(f"2. Hafıza Yanıtı: {r3}")
    print(f"3. Öğretici Analoji Uzunluğu: {len(r4)} karakter")
    print(f"4. Kod Doğrudan Kod Bloğu mu? {'Evet' if r5.strip().startswith('```') or 'import' in r5 else 'Hayır'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
