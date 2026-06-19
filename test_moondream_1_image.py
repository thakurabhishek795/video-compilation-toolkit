import urllib.request
import json
import base64
import os
import core

sheets = core.get_contact_sheets("/Users/athakur/Downloads/taliban")
img_path = os.path.join("/Users/athakur/Downloads/taliban", "contact_sheets", sheets[0])
with open(img_path, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")

payload = {
    "model": "moondream",
    "prompt": "What is this?",
    "images": [img_b64],
    "stream": False
}

req = urllib.request.Request(
    "http://localhost:11434/api/generate",
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("1 IMAGE SUCCESS:", result.get('response'))
except Exception as e:
    print("1 IMAGE ERROR:", e)

payload["images"] = [img_b64, img_b64]
req = urllib.request.Request(
    "http://localhost:11434/api/generate",
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("2 IMAGES SUCCESS:", result.get('response'))
except Exception as e:
    print("2 IMAGES ERROR:", e)
