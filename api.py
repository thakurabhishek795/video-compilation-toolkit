from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import core
from typing import List

app = FastAPI(title="Video Compilation API", version="1.0.0")

class ClipDef(BaseModel):
    video: str
    start: str
    duration: str
    out_name: str

class ExportRequest(BaseModel):
    media_dir: str
    clips: List[ClipDef]

class RenameRequest(BaseModel):
    media_dir: str
    old_name: str
    new_name: str

class SuggestRequest(BaseModel):
    media_dir: str
    video_name: str
    model: str = "llava"

class StoryboardRequest(BaseModel):
    media_dir: str
    script: str
    model: str = "llava"

class FfmpegAssistantRequest(BaseModel):
    media_dir: str
    instruction: str
    video_name: str
    out_name: str
    model: str = "llava"

class ReverseRequest(BaseModel):
    video_path: str
    out_path: str

class ResizeRequest(BaseModel):
    video_path: str
    rate: float
    out_path: str

class DownsampleRequest(BaseModel):
    video_path: str
    fps: int
    out_path: str

class ComposeRequest(BaseModel):
    main_video: str
    sub_video: str
    out_path: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Video Compilation API is running."}

@app.get("/library/videos")
def get_videos(media_dir: str):
    videos = core.get_videos(media_dir)
    return {"media_dir": media_dir, "videos": videos}

@app.post("/library/rename")
def rename_video(req: RenameRequest):
    try:
        new_name = core.rename_video(req.media_dir, req.old_name, req.new_name)
        return {"message": "Video renamed successfully.", "new_name": new_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/library/ai-suggest")
def suggest_video_name(req: SuggestRequest):
    try:
        suggested = core.suggest_video_name(req.media_dir, req.video_name, req.model)
        return {"message": "AI successfully generated a name.", "suggested_name": suggested}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/director/storyboard")
def generate_storyboard(req: StoryboardRequest):
    try:
        storyboard = core.generate_storyboard(req.media_dir, req.script, req.model)
        return {"message": "Storyboard generated successfully.", "storyboard": storyboard}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/director/ffmpeg-assistant")
def ffmpeg_assistant(req: FfmpegAssistantRequest):
    try:
        command = core.ai_ffmpeg_assistant(req.media_dir, req.instruction, req.video_name, req.out_name, req.model)
        return {"message": "FFmpeg command executed successfully.", "command": command, "file": req.out_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/library/keyframes")
def generate_keyframes(media_dir: str):
    results = core.generate_keyframes_and_sheets(media_dir)
    return {"message": "Keyframes and sheets generated.", "results": results}

@app.post("/export/clips")
def export_clips(req: ExportRequest):
    # convert pydantic models to dicts
    clips_dict = [clip.dict() for clip in req.clips]
    out_dir = core.export_individual_clips(req.media_dir, clips_dict)
    return {"message": "Clips exported successfully.", "out_dir": out_dir}

@app.post("/export/compile")
def compile_broll(req: ExportRequest):
    clips_dict = [clip.dict() for clip in req.clips]
    final_out = core.compile_unified_broll(req.media_dir, clips_dict)
    return {"message": "B-roll compiled successfully.", "file": final_out}

@app.post("/toolkit/reverse")
def reverse_video_api(req: ReverseRequest):
    try:
        core.reverse_video(req.video_path, req.out_path)
        return {"message": "Video reversed successfully.", "file": req.out_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/toolkit/resize")
def resize_video_api(req: ResizeRequest):
    try:
        core.resize_video(req.video_path, req.rate, req.out_path)
        return {"message": "Video resized successfully.", "file": req.out_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/toolkit/downsample")
def downsample_video_api(req: DownsampleRequest):
    try:
        core.downsample_video(req.video_path, req.fps, req.out_path)
        return {"message": "Video downsampled successfully.", "file": req.out_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/toolkit/compose")
def compose_video_api(req: ComposeRequest):
    try:
        core.compose_video(req.main_video, req.sub_video, req.out_path)
        return {"message": "Video composed successfully.", "file": req.out_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class MusicRequest(BaseModel):
    prompt: str
    duration: int
    api_key: str
    out_name: str
    media_dir: str

@app.post("/toolkit/music")
def generate_music_api(req: MusicRequest):
    try:
        out_path = core.generate_music(req.prompt, req.duration, req.api_key, req.out_name, req.media_dir)
        return {"message": "Music generated successfully.", "file": out_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
