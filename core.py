import os
import subprocess
import math
from PIL import Image
import urllib.request
import json
import base64
import requests

def _extract_json_array(text: str):
    start_idx = text.find('[')
    if start_idx == -1:
        return text
    
    count = 0
    in_string = False
    escape = False
    for i in range(start_idx, len(text)):
        c = text[i]
        if not escape:
            if c == '"':
                in_string = not in_string
            elif not in_string:
                if c == '[':
                    count += 1
                elif c == ']':
                    count -= 1
                    if count == 0:
                        return text[start_idx:i+1]
        if c == '\\' and not escape:
            escape = True
        else:
            escape = False
    return text[start_idx:]

def get_videos(media_dir: str):
    if not os.path.isdir(media_dir):
        return []
    return [f for f in os.listdir(media_dir) if f.endswith(".mp4") and not f.startswith(".")]

def rename_video(media_dir: str, old_name: str, new_name: str):
    if not new_name.endswith(".mp4"):
        new_name += ".mp4"
    old_path = os.path.join(media_dir, old_name)
    new_path = os.path.join(media_dir, new_name)
    if not os.path.exists(old_path):
        raise FileNotFoundError(f"Source file {old_name} not found.")
    if os.path.exists(new_path):
        raise FileExistsError(f"Destination file {new_name} already exists.")
    os.rename(old_path, new_path)
    return new_name

def suggest_video_name(media_dir: str, video_name: str, model: str = "llava"):
    vid_name = os.path.splitext(video_name)[0].replace(" ", "_")
    sheet_path = os.path.join(media_dir, "contact_sheets", f"{vid_name}_contact_sheet.jpg")
    
    if not os.path.exists(sheet_path):
        raise FileNotFoundError(f"Contact sheet for {video_name} not found. Please generate it first.")
        
    with open(sheet_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    prompt = "Analyze these video keyframes. Describe the main subject in 2 to 4 words. Use underscores instead of spaces. Do not include file extensions. Example: afghan_girls_studying"
    
    payload = {
        "model": model,
        "prompt": prompt,
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
            suggested = result.get('response', '').strip()
            # Clean up the response just in case the AI adds periods or spaces
            suggested = suggested.replace(" ", "_").replace(".", "").replace('"', '').lower()
            return suggested
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        if e.code == 404:
            raise RuntimeError("The AI model is still downloading (or not found). Please wait a few minutes for the download to finish!")
        raise RuntimeError(f"Failed to communicate with Ollama: HTTP {e.code} - {err_msg}")
    except Exception as e:
        raise RuntimeError(f"Failed to communicate with Ollama: {str(e)}")

def generate_keyframes_and_sheets(media_dir: str):
    videos = get_videos(media_dir)
    keyframes_base = os.path.join(media_dir, "keyframes")
    sheets_dir = os.path.join(media_dir, "contact_sheets")
    os.makedirs(sheets_dir, exist_ok=True)
    
    results = []
    for video in videos:
        vid_path = os.path.join(media_dir, video)
        vid_name = os.path.splitext(video)[0].replace(" ", "_")
        out_dir = os.path.join(keyframes_base, vid_name)
        os.makedirs(out_dir, exist_ok=True)
        
        # Extract keyframes (every 10s)
        fps = "1/10"
        cmd = [
            "ffmpeg", "-y", "-i", vid_path, "-vf", f"fps={fps},scale=320:-1",
            os.path.join(out_dir, "frame_%03d.jpg")
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Generate Contact Sheet
        frames = sorted([f for f in os.listdir(out_dir) if f.endswith(".jpg")])
        if frames:
            try:
                images = [Image.open(os.path.join(out_dir, f)) for f in frames]
                cols = 4
                rows = math.ceil(len(images) / cols)
                w, h = images[0].size
                sheet = Image.new('RGB', (cols * w, rows * h), (255, 255, 255))
                
                for i, img in enumerate(images):
                    x = (i % cols) * w
                    y = (i // cols) * h
                    sheet.paste(img, (x, y))
                    
                    # Draw timestamp label
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(sheet)
                    start_sec = i * 10
                    end_sec = (i + 1) * 10
                    start_str = f"{start_sec//60:02d}:{start_sec%60:02d}"
                    end_str = f"{end_sec//60:02d}:{end_sec%60:02d}"
                    text = f" {start_str} - {end_str} "
                    
                    draw.rectangle([x, y, x + 105, y + 25], fill="black")
                    draw.text((x + 5, y + 5), text, fill="white")
                
                sheet_path = os.path.join(sheets_dir, f"{vid_name}_contact_sheet.jpg")
                sheet.save(sheet_path)
                results.append(f"Sheet generated for {video}")
            except Exception as e:
                results.append(f"Error creating sheet for {video}: {e}")
    return results

def get_contact_sheets(media_dir: str):
    sheets_dir = os.path.join(media_dir, "contact_sheets")
    if not os.path.isdir(sheets_dir):
        return []
    return [f for f in os.listdir(sheets_dir) if f.endswith(".jpg")]

def export_individual_clips(media_dir: str, clips: list):
    out_dir = os.path.join(media_dir, "exported_clips")
    os.makedirs(out_dir, exist_ok=True)
    for i, clip in enumerate(clips):
        input_path = os.path.join(media_dir, clip['video'])
        temp_cut = os.path.join(out_dir, f"temp_{i}.mp4")
        output_path = os.path.join(out_dir, clip['out_name'])
        
        subprocess.run(["ffmpeg", "-y", "-ss", clip['start'], "-i", input_path, "-t", clip['duration'], "-c", "copy", temp_cut], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-i", temp_cut, "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p", "-r", "25", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(temp_cut): os.remove(temp_cut)
    return out_dir

def compile_unified_broll(media_dir: str, clips: list):
    out_dir = os.path.join(media_dir, "exported_clips")
    os.makedirs(out_dir, exist_ok=True)
    concat_list_path = os.path.join(out_dir, "concat_list.txt")
    
    with open(concat_list_path, "w") as f:
        for i, clip in enumerate(clips):
            input_path = os.path.join(media_dir, clip['video'])
            temp_cut = os.path.join(out_dir, f"temp_{i}.mp4")
            output_path = os.path.join(out_dir, f"norm_{i}.mp4")
            
            subprocess.run(["ffmpeg", "-y", "-ss", clip['start'], "-i", input_path, "-t", clip['duration'], "-c", "copy", temp_cut], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["ffmpeg", "-y", "-i", temp_cut, "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p", "-r", "25", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(temp_cut): os.remove(temp_cut)
            
            f.write(f"file '{output_path}'\n")
    
    final_out = os.path.join(media_dir, "final_broll_compilation.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", final_out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    for i in range(len(clips)):
        norm_path = os.path.join(out_dir, f"norm_{i}.mp4")
        if os.path.exists(norm_path): os.remove(norm_path)
    if os.path.exists(concat_list_path): os.remove(concat_list_path)
    return final_out

def generate_storyboard(media_dir: str, script: str, model: str = "llava"):
    sheet_files = sorted(get_contact_sheets(media_dir))
    if not sheet_files:
        raise FileNotFoundError("No contact sheets found in the library. Please generate them first.")

    # HYBRID APPROACH: If moondream or deepseek is selected, use Moondream for vision and Deepseek for JSON
    if model in ["moondream", "deepseek-coder-v2"]:
        captions = []
        for i, sf in enumerate(sheet_files):
            vid_name = sf.replace("_contact_sheet.jpg", "") + ".mp4"
            with open(os.path.join(media_dir, "contact_sheets", sf), "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            
            payload = {
                "model": "moondream",
                "prompt": "Describe this keyframe collage in 1 sentence. Focus on the visual subjects.",
                "images": [img_b64],
                "stream": False
            }
            req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    cap = res.get("response", "").strip()
                    captions.append(f"Image {i+1} ({vid_name}): {cap}")
            except Exception:
                captions.append(f"Image {i+1} ({vid_name}): (Visual analysis failed)")

        mapping_text = "\n".join(captions)
        
        prompt = f"""You are an expert AI Film Director. 
I have a script and a list of videos with their visual descriptions:
{mapping_text}

Script:
\"\"\"{script}\"\"\"

Break the script down into logical scenes. Choose the most visually appropriate video file from the list for each scene.
Output your response as a RAW JSON array. Do not wrap the JSON in markdown blocks. Do not add conversational text.
Format:
[
  {{
    "scene_number": 1,
    "script_segment": "exact text from script",
    "visual_concept": "describe what we see",
    "suggested_clip": "filename.mp4",
    "start_time": "00:00:00",
    "duration": "00:00:10",
    "editing_tips": "e.g., slow zoom, cut on action"
  }}
]"""
        # Force Deepseek for perfect JSON formatting
        text_model = "deepseek-coder-v2"

        payload = {
            "model": text_model,
            "prompt": prompt,
            "stream": False
        }
    else:
        # STANDARD APPROACH (e.g. for llava)
        images_b64 = []
        file_mapping = []
        for i, sf in enumerate(sheet_files):
            vid_name = sf.replace("_contact_sheet.jpg", "") + ".mp4"
            file_mapping.append(f"Image {i+1}: {vid_name}")
            with open(os.path.join(media_dir, "contact_sheets", sf), "rb") as f:
                images_b64.append(base64.b64encode(f.read()).decode("utf-8"))
                
        mapping_text = "\n".join(file_mapping)
        
        prompt = f"""You are an expert AI Film Director. 
I have provided you with a script, and {len(images_b64)} contact sheets (visual grids of keyframes) from my available video library. 
The contact sheets are provided as images in the following order:
{mapping_text}

Here is the script:
\"\"\"{script}\"\"\"

Break the script down into logical scenes. For each scene, review the contact sheets and choose the most visually appropriate video file from the list.
Output your response as a RAW JSON array. Do not wrap the JSON in markdown blocks. Do not add any conversational text.
Format:
[
  {{
    "scene_number": 1,
    "script_segment": "exact text from script",
    "visual_concept": "describe what we see",
    "suggested_clip": "filename.mp4",
    "start_time": "00:00:00",
    "duration": "00:00:10",
    "editing_tips": "e.g., slow zoom, cut on action"
  }}
]"""

        payload = {
            "model": model,
            "prompt": prompt,
            "images": images_b64,
            "stream": False,
            "options": {
                "num_ctx": 8192,
                "temperature": 0.2
            }
        }
        
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            suggested = result.get('response', '').strip()
            
            clean_json = _extract_json_array(suggested)
                
            return json.loads(clean_json.strip(), strict=False)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        raise RuntimeError(f"Failed to communicate with Ollama: HTTP {e.code} - {err_msg}")
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error Details: {e}")
        print(f"Clean JSON was: {repr(clean_json)}")
        raise ValueError(f"AI failed to return valid JSON.\nError: {e}\nCleaned JSON: {clean_json}\nRaw output: {suggested}")
    except Exception as e:
        raise RuntimeError(f"Storyboard generation failed: {str(e)}")

def ai_ffmpeg_assistant(media_dir: str, instruction: str, video_name: str, out_name: str, model: str = "llava"):
    input_path = os.path.join(media_dir, video_name)
    out_path = os.path.join(media_dir, out_name)
    
    system_prompt = """You are an FFmpeg expert. Generate the appropriate FFmpeg command based on the user instructions.
【Rules】
- Output ONLY the ffmpeg command on one line.
- Do NOT provide any explanations, code blocks, or comments.
- Use the exact input and output file paths provided.
- Do not use non-existent options.
- Use safe encoding settings (libx264, aac, etc.)."""
    
    user_prompt = f"""【User Instruction】
{instruction}

【Input File】
{input_path}

【Output File】
{out_path}

Based on the instructions above, output the FFmpeg command on a single line. Start with "ffmpeg"."""
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": f"{system_prompt}\n\n{user_prompt}",
        "stream": False
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            command = result.get('response', '').strip()
            
            # Clean markdown block if the model ignores the prompt instruction
            if command.startswith("```bash"):
                command = command[7:]
            elif command.startswith("```"):
                command = command[3:]
            if command.endswith("```"):
                command = command[:-3]
            command = command.strip()
            
            # Extract just the ffmpeg command if it hallucinated more text
            lines = command.split('\n')
            for line in lines:
                if line.strip().startswith('ffmpeg'):
                    command = line.strip()
                    break
            
            if not command.startswith("ffmpeg"):
                raise RuntimeError(f"AI failed to generate a valid FFmpeg command. Raw output: {command}")
                
            # Execute the generated command
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return command
            
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to communicate with Ollama: HTTP {e.code}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to execute generated FFmpeg command: {e.stderr.decode('utf-8')}\nCommand was: {command}")
    except Exception as e:
        raise RuntimeError(f"AI Assistant failed: {str(e)}")

def generate_music(prompt: str, duration: int, api_key: str, out_name: str, media_dir: str):
    """
    Generates background music using ACE-Step API based on the text prompt.
    """
    url = "https://api.acemusic.ai/v1/chat/completions"
    
    payload = {
        "messages": [{"role": "user", "content": f"<prompt>{prompt}</prompt>"}],
        "stream": False,
        "thinking": True,
        "audio_config": {
            "duration": duration,
            "format": "mp3",
            "vocal_language": "en"
        },
        "model": "acemusic/acestep-v1.5-xl-turbo"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=600)
        
        if response.status_code != 200:
            raise RuntimeError(f"ACE-Step API error (HTTP {response.status_code}): {response.text[:500]}")
            
        result = response.json()
        
        choices = result.get("choices", [])
        if not choices:
            raise RuntimeError("No choices in API response")
        
        message = choices[0].get("message", {})
        audio_list = message.get("audio", [])
        
        if not audio_list:
            raise RuntimeError(f"No audio in API response. Message: {message.get('content', '')}")
            
        audio_url = audio_list[0].get("audio_url", {}).get("url", "")
        if not audio_url.startswith("data:audio"):
            raise RuntimeError("Unexpected audio format in response")
            
        b64_data = audio_url.split(",", 1)[1]
        audio_bytes = base64.b64decode(b64_data)
        
        out_path = os.path.join(media_dir, out_name)
        with open(out_path, "wb") as f:
            f.write(audio_bytes)
            
        return out_path
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"ACE-Step API error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Music generation failed: {str(e)}")
