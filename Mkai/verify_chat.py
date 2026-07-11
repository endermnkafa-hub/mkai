import json
import urllib.request

payload = {
    "message": "merhaba",
    "provider": "ollama",
    "model": "qwen2.5:14b",
    "history": []
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/chat",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req, timeout=120) as resp:
    print(resp.status)
    print(resp.read().decode("utf-8"))
