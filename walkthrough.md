# Video Compilation Toolkit - Walkthrough

The Video Compilation Toolkit is now fully decoupled! It runs both a visual web application for you, and a headless API layer for AI agents like me.

## Human Interface (Streamlit)
Open your web browser and navigate to:
**[http://localhost:8501](http://localhost:8501)**

Use this UI to visually browse your folders, view contact sheets, and manually queue up exports. You can also use the **✨ Auto-Suggest Name** button to have a local AI Vision model (`LLaVA`) analyze your videos and instantly suggest descriptive filenames!

## Agentic AI Interface (FastAPI)
The API server is running in the background at:
**[http://localhost:8000](http://localhost:8000)**

### How AI Agents interact with the Toolkit
Because we built this using FastAPI, it automatically generates a machine-readable OpenAPI specification. You or an AI agent can browse the interactive documentation here:
**[http://localhost:8000/docs](http://localhost:8000/docs)**

### Example AI Request
An AI agent can now write a simple script or issue a `curl` command to compile a video for you automatically:

```bash
curl -X POST "http://localhost:8000/export/compile" \
     -H "Content-Type: application/json" \
     -d '{
           "media_dir": "/Users/athakur/Downloads/taliban",
           "clips": [
             {"video": "12647598_1920_1080_50fps.mp4", "start": "00:00:00", "duration": "00:00:04", "out_name": "c1.mp4"},
             {"video": "FRANCE 24 report.mp4", "start": "00:00:12", "duration": "00:00:05", "out_name": "c2.mp4"}
           ]
         }'
```
