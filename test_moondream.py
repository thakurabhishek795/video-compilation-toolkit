import urllib.request
import json
import base64
import os
import core

sheets = core.get_contact_sheets("/Users/athakur/Downloads/taliban")

images_b64 = []
for sf in sheets:
    with open(os.path.join("/Users/athakur/Downloads/taliban", "contact_sheets", sf), "rb") as f:
        images_b64.append(base64.b64encode(f.read()).decode("utf-8"))

payload = {
    "model": "moondream",
    "prompt": "What is this?",
    "images": images_b64,
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
        print("SUCCESS")
except urllib.error.HTTPError as e:
    print("ERROR:", e.code, e.read().decode('utf-8'))
