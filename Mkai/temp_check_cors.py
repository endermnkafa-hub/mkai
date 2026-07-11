import urllib.request

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/chat',
    method='OPTIONS',
    headers={
        'Origin': 'http://127.0.0.1:3001',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type',
    },
)

try:
    resp = urllib.request.urlopen(req)
    print(resp.status)
    print(resp.headers.get('access-control-allow-origin'))
except Exception as e:
    print(type(e).__name__, e)
