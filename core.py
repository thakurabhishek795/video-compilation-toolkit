import os
import subprocess
import math
from PIL import Image
import urllib.request
import json
import base64
import requests
import difflib
import csv
from datetime import datetime

def _extract_json_object(text: str):
    start_idx = text.find('{')
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
                if c == '{':
                    count += 1
                elif c == '}':
                    count -= 1
                    if count == 0:
                        return text[start_idx:i+1]
        if c == '\\' and not escape:
            escape = True
        else:
            escape = False
    return text

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

def get_media_files(media_dir: str):
    if not os.path.isdir(media_dir):
        return []
    ignore_list = ["final_broll_compilation", "ai_test_output", "afghanistan_broll"]
    valid_exts = (".mp4", ".mov", ".jpg", ".jpeg", ".png")
    return [f for f in os.listdir(media_dir) if f.lower().endswith(valid_exts) and not f.startswith(".") and not any(ign in f.lower() for ign in ignore_list)]

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

def batch_rename_videos_safely(media_dir: str, rename_mapping: dict):
    """
    Safely renames multiple videos using a two-phase approach to avoid conflicts.
    Generates a CSV manifest audit trail.
    rename_mapping: dict of {old_filename: new_filename}
    """
    tmp_mapping = {}
    
    # Pre-flight check and ensure .mp4
    for old_name, new_name in rename_mapping.items():
        if not new_name.endswith(".mp4"):
            new_name += ".mp4"
            rename_mapping[old_name] = new_name
            
        old_path = os.path.join(media_dir, old_name)
        if not os.path.exists(old_path):
            raise FileNotFoundError(f"Source file {old_name} not found.")
            
        # We don't check for new_path existence yet because it might be another old_name being renamed in this batch!
        
        tmp_name = old_name + ".renaming_tmp"
        tmp_mapping[old_name] = tmp_name

    # Phase 1: Rename all to .renaming_tmp
    for old_name, tmp_name in tmp_mapping.items():
        old_path = os.path.join(media_dir, old_name)
        tmp_path = os.path.join(media_dir, tmp_name)
        os.rename(old_path, tmp_path)
        
    # Phase 2: Rename all .renaming_tmp to final names
    for old_name, new_name in rename_mapping.items():
        tmp_name = tmp_mapping[old_name]
        tmp_path = os.path.join(media_dir, tmp_name)
        new_path = os.path.join(media_dir, new_name)
        
        # If destination exists now, it's a conflict!
        if os.path.exists(new_path):
            raise FileExistsError(f"Destination file {new_name} already exists. Some files may be stuck as .renaming_tmp!")
            
        os.rename(tmp_path, new_path)

    # Generate CSV Audit Trail
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    manifest_name = f"video_rename_manifest_{timestamp}.csv"
    manifest_path = os.path.join(media_dir, manifest_name)
    
    with open(manifest_path, 'w', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Original Name', 'New Name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for old_name, new_name in rename_mapping.items():
            writer.writerow({
                'Timestamp': timestamp,
                'Original Name': old_name,
                'New Name': new_name
            })
            
    return manifest_path

def suggest_video_name(media_dir: str, video_name: str, model: str = "llava"):
    if model == "moondream":
        model = "moondream-large"
        
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

def generate_keyframes_and_sheets(media_dir: str, progress_callback=None):
    media_files = get_media_files(media_dir)
    keyframes_base = os.path.join(media_dir, "keyframes")
    sheets_dir = os.path.join(media_dir, "contact_sheets")
    os.makedirs(sheets_dir, exist_ok=True)
    
    results = []
    total_files = len(media_files)
    for i, media_file in enumerate(media_files):
        if progress_callback:
            progress_callback(i / max(1, total_files), f"Processing {media_file}...")
            
        file_path = os.path.join(media_dir, media_file)
        file_name = os.path.splitext(media_file)[0].replace(" ", "_")
        out_dir = os.path.join(keyframes_base, file_name)
        os.makedirs(out_dir, exist_ok=True)
        
        is_image = media_file.lower().endswith((".jpg", ".jpeg", ".png"))
        
        if is_image:
            # For images, just copy the image as the single keyframe
            import shutil
            dest_frame = os.path.join(out_dir, "frame_001.jpg")
            shutil.copy2(file_path, dest_frame)
        else:
            # Extract keyframes (every 10s)
            fps = "1/10"
            cmd = [
                "ffmpeg", "-y", "-i", file_path, "-vf", f"fps={fps},scale=320:-1",
                os.path.join(out_dir, "frame_%03d.jpg")
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"Failed to extract frames for {media_file}: {res.stderr}")
        
        # Generate Contact Sheet
        frames = sorted([f for f in os.listdir(out_dir) if f.endswith(".jpg")])
        if frames:
            try:
                images = [Image.open(os.path.join(out_dir, f)) for f in frames]
                cols = 4
                rows = math.ceil(len(images) / cols)
                w, h = images[0].size
                sheet = Image.new('RGB', (cols * w, rows * h), (255, 255, 255))
                
                timestamps = []
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
                    text = f" {video} | {start_str} - {end_str} "
                    timestamps.append(text.strip())
                    
                    width = 105 + (len(video) * 6)
                    draw.rectangle([x, y, x + width, y + 25], fill="black")
                    draw.text((x + 5, y + 5), text, fill="white")
                
                sheet_path = os.path.join(sheets_dir, f"{vid_name}_contact_sheet.jpg")
                exif = sheet.getexif()
                exif[37510] = f"Video: {video} | Timestamps: {', '.join(timestamps)}"
                sheet.save(sheet_path, exif=exif)
                results.append(f"Sheet generated for {video}")
            except Exception as e:
                results.append(f"Error creating sheet for {video}: {e}")
    if progress_callback:
        progress_callback(1.0, "Finished generating all Keyframes and Contact Sheets!")
    return results

def get_contact_sheets(media_dir: str):
    sheets_dir = os.path.join(media_dir, "contact_sheets")
    if not os.path.isdir(sheets_dir):
        return []
    return [f for f in os.listdir(sheets_dir) if f.endswith(".jpg")]

def export_individual_clips(media_dir: str, clips: list):
    out_dir = os.path.join(media_dir, "exported_clips")
    os.makedirs(out_dir, exist_ok=True)
    for clip in clips:
        input_path = os.path.join(media_dir, clip['File Name'])
        output_path = os.path.join(out_dir, clip['Output Name'])
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", clip['Start Time'],
            "-i", input_path,
            "-t", clip['Duration'],
            "-c", "copy",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    return out_dir

def compile_unified_broll(media_dir: str, clips: list, burn_captions: bool = False):
    out_dir = os.path.join(media_dir, "exported_clips")
    os.makedirs(out_dir, exist_ok=True)
    concat_list_path = os.path.join(out_dir, "concat_list.txt")
    
    with open(concat_list_path, "w") as f:
        for i, clip in enumerate(clips):
            input_path = os.path.join(media_dir, clip['File Name'])
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Source file not found: {clip['File Name']}. This is likely a hallucinated clip from an older storyboard generation. Please CLEAR your Queue and generate a new storyboard.")
            
            temp_cut = os.path.join(out_dir, f"temp_{i}.mp4")
            output_path = os.path.join(out_dir, f"norm_{i}.mp4")
            
            is_image = input_path.lower().endswith((".jpg", ".jpeg", ".png"))
            
            if is_image:
                # For images, create a 5-second video
                res1 = subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", input_path, "-t", "5", "-c:v", "libx264", temp_cut], capture_output=True, text=True)
                if res1.returncode != 0: raise RuntimeError(f"FFMPEG Error (image loop): {res1.stderr}")
            else:
                res1 = subprocess.run(["ffmpeg", "-y", "-ss", str(clip.get('Start Time', '0')), "-i", input_path, "-t", str(clip.get('Duration', '5')), "-c", "copy", temp_cut], capture_output=True, text=True)
                if res1.returncode != 0: raise RuntimeError(f"FFMPEG Error (cut): {res1.stderr}")
            
            # Smart formatting: blurred background for vertical video, scale to 1920x1080
            # Base filter chain for scaling/padding
            base_filter = "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease[fg];[0:v]scale=1920:1080:force_original_aspect_ratio=increase,boxblur=20:20[bg];[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[out]"
            
            # If burn_captions is True and caption exists, append drawtext
            caption = clip.get('Caption', '')
            if burn_captions and caption:
                # Clean caption for ffmpeg string escaping
                caption_clean = caption.replace("'", "").replace(":", "")
                # Draw text centered at the bottom, white with a black shadow
                drawtext_filter = f",drawtext=text='{caption_clean}':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=h-th-80:shadowcolor=black:shadowx=2:shadowy=2[out2]"
                base_filter = base_filter.replace("[out]", "[tmpout]") + drawtext_filter.replace("[out2]", "[out]")
                filter_cmd = ["-filter_complex", base_filter, "-map", "[out]"]
            else:
                filter_cmd = ["-filter_complex", base_filter.replace("[out]", ""), "-map", "[out]"] # Note: The original base filter outputs to [out] implicitly if we just use -vf, but we are using filter_complex
                # Actually, simpler filter_complex:
                filter_cmd = ["-filter_complex", base_filter, "-map", "[out]"]
            
            # Re-encode video
            encode_cmd = ["ffmpeg", "-y", "-i", temp_cut] + filter_cmd + ["-r", "30", "-an", "-c:v", "libx264", output_path]
            res2 = subprocess.run(encode_cmd, capture_output=True, text=True)
            if res2.returncode != 0: raise RuntimeError(f"FFMPEG Error (scale/format): {res2.stderr}")
            
            if os.path.exists(temp_cut): os.remove(temp_cut)
            
            f.write(f"file '{output_path}'\n")
    
    final_out = os.path.join(media_dir, "final_broll_compilation.mp4")
    res3 = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", final_out], capture_output=True, text=True)
    if res3.returncode != 0: raise RuntimeError(f"FFMPEG Error (concat): {res3.stderr}")
    
    for i in range(len(clips)):
        norm_path = os.path.join(out_dir, f"norm_{i}.mp4")
        if os.path.exists(norm_path): os.remove(norm_path)
    if os.path.exists(concat_list_path): os.remove(concat_list_path)
    return final_out

def verify_compilation(filepath: str):
    """
    Runs ffprobe to verify the final compiled file.
    Returns a dict with QA metrics.
    """
    if not os.path.exists(filepath):
        return {"Status": "Failed - File not found"}
        
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate,codec_name", "-show_entries", "format=duration", "-of", "json", filepath]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return {"Status": f"Failed - ffprobe error: {res.stderr}"}
        
    try:
        data = json.loads(res.stdout)
        stream = data['streams'][0]
        fmt = data['format']
        
        # Parse frame rate (e.g. "30/1")
        fps_str = stream.get('r_frame_rate', '0/0')
        parts = fps_str.split('/')
        if len(parts) == 2 and int(parts[1]) != 0:
            fps = round(int(parts[0]) / int(parts[1]), 2)
        else:
            fps = 0
            
        return {
            "Status": "Passed",
            "Duration (sec)": round(float(fmt.get('duration', 0)), 2),
            "Resolution": f"{stream.get('width', 0)}x{stream.get('height', 0)}",
            "FPS": fps,
            "Codec": stream.get('codec_name', 'unknown')
        }
    except Exception as e:
        return {"Status": f"Failed - parse error: {str(e)}"}

def generate_storyboard(media_dir: str, script: str, model: str = "llava", stream_callback=None):
    sheet_files = sorted(get_contact_sheets(media_dir))
    if not sheet_files:
        raise FileNotFoundError("No contact sheets found in the library. Please generate them first.")

    media_files = get_media_files(media_dir)
    reverse_map = {os.path.splitext(v)[0].replace(" ", "_"): v for v in media_files}

    # HYBRID APPROACH: If moondream or deepseek is selected, use Moondream for vision and Deepseek for JSON
    if model in ["moondream", "deepseek-coder-v2"]:
        captions = []
        for i, sf in enumerate(sheet_files):
            underscored_vid_name = sf.replace("_contact_sheet.jpg", "")
            real_vid_name = reverse_map.get(underscored_vid_name, underscored_vid_name + ".mp4")
            with open(os.path.join(media_dir, "contact_sheets", sf), "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            
            
            if stream_callback:
                stream_callback(f"Visual analysis: Processing {real_vid_name}...")
                
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
                    captions.append(f"Image {i+1} ({real_vid_name}): {cap}")
            except Exception:
                captions.append(f"Image {i+1} ({real_vid_name}): (Visual analysis failed)")

        mapping_text = "\n".join(captions)
        
        prompt = f"""You are an expert AI Film Director. 
I have a script and a list of videos with their visual descriptions:
{mapping_text}

Script:
\"\"\"{script}\"\"\"

Break the script down into an Event-Based storyboard. Output your response as a RAW JSON object. Do not wrap the JSON in markdown blocks. Do not add conversational text. Use actions: insert_broll, music_change, transition, text_overlay. For each clip, generate a 'caption' that summarizes the script beat into a short, punchy, poetic phrase (e.g., 'Behind closed doors').
Format:
{{
  "metadata": {{
    "video_id": "auto",
    "duration_sec": 0,
    "generated_by": "deepseek-coder-v2"
  }},
  "storyboard": [
    {{
      "timestamp": "0:00",
      "timestamp_sec": 0.0,
      "action": "insert_broll",
      "subtype": "none",
      "description": "Visual description and reason",
      "source_start_timestamp": "00:00:00",
      "duration_suggestion_sec": 10.0,
      "caption": "Short punchy poetic beat",
      "confidence": 0.9,
      "priority": "high",
      "suggested_clip": "filename.mp4"
    }}
  ],
  "summary": {{
    "total_suggestions": 1,
    "high_priority": 1,
    "medium_priority": 0,
    "estimated_edit_time_min": 5
  }}
}}"""
        # Force Deepseek for perfect JSON formatting
        text_model = "deepseek-coder-v2"

        payload = {
            "model": text_model,
            "prompt": prompt,
            "stream": True if stream_callback else False
        }
    else:
        # STANDARD APPROACH (e.g. for llava)
        images_b64 = []
        file_mapping = []
        for i, sf in enumerate(sheet_files):
            underscored_vid_name = sf.replace("_contact_sheet.jpg", "")
            real_vid_name = reverse_map.get(underscored_vid_name, underscored_vid_name + ".mp4")
            file_mapping.append(f"Image {i+1}: {real_vid_name}")
            with open(os.path.join(media_dir, "contact_sheets", sf), "rb") as f:
                images_b64.append(base64.b64encode(f.read()).decode("utf-8"))
                
        mapping_text = "\n".join(file_mapping)
        
        prompt = f"""You are an expert AI Film Director. 
I have provided you with a script, and {len(images_b64)} contact sheets (visual grids of keyframes) from my available video library. 
The contact sheets are provided as images in the following order:
{mapping_text}

Here is the script:
\"\"\"{script}\"\"\"

Break the script down into an Event-Based storyboard. For each event, review the contact sheets and choose the most visually appropriate video file from the list. 
IMPORTANT: Look at the text printed on the specific frame you chose. Extract the start timestamp (e.g. "00:01:00") and put it into the `source_start_timestamp` field.
Output your response as a RAW JSON object. Do not wrap the JSON in markdown blocks. Do not add any conversational text. Use actions: insert_broll, music_change, transition, text_overlay. For each clip, generate a 'caption' that summarizes the script beat into a short, punchy, poetic phrase (e.g., 'Behind closed doors').
Format:
{{
  "metadata": {{
    "video_id": "auto",
    "duration_sec": 0,
    "generated_by": "llava"
  }},
  "storyboard": [
    {{
      "timestamp": "0:00",
      "timestamp_sec": 0.0,
      "action": "insert_broll",
      "subtype": "none",
      "description": "Visual description and reason",
      "source_start_timestamp": "00:00:00",
      "duration_suggestion_sec": 10.0,
      "caption": "Short punchy poetic beat",
      "confidence": 0.9,
      "priority": "high",
      "suggested_clip": "filename.mp4"
    }}
  ],
  "summary": {{
    "total_suggestions": 1,
    "high_priority": 1,
    "medium_priority": 0,
    "estimated_edit_time_min": 5
  }}
}}"""

        payload = {
            "model": model,
            "prompt": prompt,
            "images": images_b64,
            "stream": True if stream_callback else False,
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
            if payload.get("stream"):
                full_text = ""
                for line in response:
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        full_text += chunk.get("response", "")
                        if stream_callback:
                            stream_callback(full_text)
                suggested = full_text.strip()
            else:
                result = json.loads(response.read().decode('utf-8'))
                suggested = result.get('response', '').strip()
            
            clean_json = _extract_json_object(suggested)
            data = json.loads(clean_json.strip(), strict=False)
            if "storyboard" in data:
                mapping = {}
                for idx, sf in enumerate(sheet_files):
                    underscored_vid_name = sf.replace("_contact_sheet.jpg", "")
                    real_vid_name = reverse_map.get(underscored_vid_name, underscored_vid_name + ".mp4")
                    mapping[f"Image {idx+1}"] = real_vid_name
                
                real_names = list(mapping.values())
                
                for event in data["storyboard"]:
                    clip = str(event.get("suggested_clip", ""))
                    # Exact Match (by Image Number)
                    if clip in mapping:
                        event["suggested_clip"] = mapping[clip]
                        continue
                        
                    # Exact Match (by Real Name)
                    if clip in real_names:
                        continue
                        
                    # Fuzzy match the filename
                    matches = difflib.get_close_matches(clip, real_names, n=1, cutoff=0.3)
                    if matches:
                        event["suggested_clip"] = matches[0]
                        continue
                        
                    # Fallback mapping
                    matched = False
                    for img_label, actual_filename in mapping.items():
                        if clip.startswith(img_label) or actual_filename in clip or clip in actual_filename:
                            event["suggested_clip"] = actual_filename
                            matched = True
                            break
                            
                    if not matched and real_names:
                        event["suggested_clip"] = real_names[0]
            return data
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

def generate_fcpxml(media_dir: str, clips: list):
    import xml.etree.ElementTree as ET
    from xml.dom import minidom
    import os

    def sec_to_fcpxml_time(time_str):
        if not time_str or time_str == "Unknown":
            return "0s"
        parts = time_str.split(":")
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            total_sec = h * 3600 + m * 60 + s
            if total_sec == int(total_sec):
                return f"{int(total_sec)}s"
            return f"{int(total_sec * 1000)}/1000s"
        return "0s"

    fcpxml = ET.Element("fcpxml", version="1.9")
    resources = ET.SubElement(fcpxml, "resources")
    ET.SubElement(resources, "format", id="r1", name="FFVideoFormat1080p25", frameDuration="1/25s", width="1920", height="1080")

    library = ET.SubElement(fcpxml, "library")
    event = ET.SubElement(library, "event", name="B-Roll Compilation")
    project = ET.SubElement(event, "project", name="Unified Storyboard")
    sequence = ET.SubElement(project, "sequence", format="r1", tcStart="0s", tcFormat="NDF")
    spine = ET.SubElement(sequence, "spine")

    assets = {}
    asset_idx = 2
    current_offset_sec = 0.0

    for clip in clips:
        filename = clip['File Name']
        if filename not in assets:
            abs_path = os.path.abspath(os.path.join(media_dir, filename))
            asset_id = f"r{asset_idx}"
            assets[filename] = asset_id
            asset_idx += 1
            ET.SubElement(resources, "asset", id=asset_id, name=filename, src=f"file://{abs_path}", hasVideo="1", hasAudio="1")
        else:
            asset_id = assets[filename]

        start_sec_str = sec_to_fcpxml_time(clip['Start Time'])
        duration_sec_str = sec_to_fcpxml_time(clip['Duration'])
        
        dur_parts = clip['Duration'].split(":")
        dur_val = int(dur_parts[0])*3600 + int(dur_parts[1])*60 + float(dur_parts[2]) if len(dur_parts) == 3 else 0.0
        
        offset_sec_str = f"{int(current_offset_sec * 1000)}/1000s" if current_offset_sec != int(current_offset_sec) else f"{int(current_offset_sec)}s"
        
        ET.SubElement(spine, "asset-clip", ref=asset_id, offset=offset_sec_str, name=filename, start=start_sec_str, duration=duration_sec_str, format="r1")
        
        current_offset_sec += dur_val

    xml_str = ET.tostring(fcpxml, 'utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="    ")
    
    return '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n' + '\n'.join(pretty_xml.split('\n')[1:])

def generate_edl(clips: list, fps: int = 25):
    lines = [
        "TITLE:   UNIFIED_STORYBOARD",
        "FCM: NON-DROP FRAME",
        ""
    ]
    
    def sec_to_tc(total_sec):
        h = int(total_sec // 3600)
        m = int((total_sec % 3600) // 60)
        s = int(total_sec % 60)
        f = int(round((total_sec - int(total_sec)) * fps))
        if f >= fps:
            s += 1
            f -= fps
        return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"

    record_in_sec = 0.0
    
    for i, clip in enumerate(clips):
        parts = clip.get('Start Time', '00:00:00').split(":")
        start_sec = 0.0
        if len(parts) == 3:
            start_sec = int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
            
        dur_parts = clip.get('Duration', '00:00:00').split(":")
        dur_sec = 0.0
        if len(dur_parts) == 3:
            dur_sec = int(dur_parts[0])*3600 + int(dur_parts[1])*60 + float(dur_parts[2])
            
        start_tc = sec_to_tc(start_sec)
        end_tc = sec_to_tc(start_sec + dur_sec)
        
        rec_in_tc = sec_to_tc(record_in_sec)
        rec_out_tc = sec_to_tc(record_in_sec + dur_sec)
        
        event_num = f"{i+1:03d}"
        
        lines.append(f"{event_num}  AX       V     C        {start_tc} {end_tc} {rec_in_tc} {rec_out_tc}")
        lines.append(f"* FROM CLIP NAME: {clip['File Name']}")
        lines.append("")
        
        
    return "\n".join(lines)

def run_audio_pipeline(media_dir: str, video_filename: str, progress_callback=None):
    import os
    from audio.audio_pipeline import AudioIntelligencePipeline
    
    video_path = os.path.join(media_dir, video_filename)
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Source video not found: {video_path}")
        
    output_dir = os.path.join(media_dir, "audio_reports")
    
    pipeline = AudioIntelligencePipeline(
        video_path=video_path,
        whisper_model_size="base",
        output_dir=output_dir,
        max_workers=5
    )
    
    return pipeline.run(progress_callback=progress_callback)

