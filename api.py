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
        suggested = core.suggest_video_name(req.media_dir, req.video_name)
        return {"message": "AI successfully generated a name.", "suggested_name": suggested}
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
