import os
import subprocess
import math
from PIL import Image
import urllib.request
import json
import base64

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

def suggest_video_name(media_dir: str, video_name: str):
    vid_name = os.path.splitext(video_name)[0].replace(" ", "_")
    sheet_path = os.path.join(media_dir, "contact_sheets", f"{vid_name}_contact_sheet.jpg")
    
    if not os.path.exists(sheet_path):
        raise FileNotFoundError(f"Contact sheet for {video_name} not found. Please generate it first.")
        
    with open(sheet_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    prompt = "Analyze these video keyframes. Describe the main subject in 2 to 4 words. Use underscores instead of spaces. Do not include file extensions. Example: afghan_girls_studying"
    
    payload = {
        "model": "llava",
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
        if e.code == 404:
            raise RuntimeError("The AI model is still downloading (or not found). Please wait a few minutes for the download to finish!")
        raise RuntimeError(f"Failed to communicate with Ollama: HTTP {e.code}")
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
