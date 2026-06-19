import base64
import os
import json
import urllib.request
import core

def get_caption(img_path):
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    payload = {
        "model": "moondream",
        "prompt": "Describe this keyframe collage in 1 sentence.",
        "images": [img_b64],
        "stream": False
    }
    req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result.get("response", "").strip()

media_dir = "/Users/athakur/Downloads/taliban"
sheets = core.get_contact_sheets(media_dir)
captions = []
for sf in sheets:
    cap = get_caption(os.path.join(media_dir, "contact_sheets", sf))
    vid_name = sf.replace("_contact_sheet.jpg", "") + ".mp4"
    captions.append(f"Video: {vid_name} | Description: {cap}")

prompt = f"""You are an expert AI Film Director. 
I have a script and a list of videos with their visual descriptions:
{chr(10).join(captions)}

Script:
"In Dari, the national language of Afghanistan, Noor means light. Yet, a profound darkness has fallen over Afghanistan’s girls and women."

Break the script down into logical scenes. Choose the most visually appropriate video file from the list for each scene.
Output RAW JSON array:
[
  {{
    "scene_number": 1,
    "script_segment": "...",
    "visual_concept": "...",
    "suggested_clip": "filename.mp4",
    "editing_tips": "..."
  }}
]"""

payload = {
    "model": "deepseek-coder-v2",
    "prompt": prompt,
    "stream": False
}
req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    result = json.loads(response.read().decode('utf-8'))
    print(result.get("response", ""))
