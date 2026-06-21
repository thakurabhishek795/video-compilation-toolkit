# System Architecture

The Video Compilation Toolkit follows a clean separation of concerns, divided primarily between a Streamlit frontend and a Python backend, supported by local AI intelligence pipelines.

## 1. Frontend (`app.py`)
The frontend is built with **Streamlit** and acts as the user's interactive workspace.
- **State Management:** It heavily utilizes `st.session_state` to store temporary data like the user's `clips` (the editing queue) and the `storyboard` (the AI's suggested timeline).
- **Core Tabs & Sections:**
  - Media Directory ingestion.
  - Video Pre-Processing (Contact Sheets & Summaries).
  - Editing Queue & Compilation (Stitching via FFmpeg).
  - AI Director (Script to Storyboard & Audio Intelligence).

## 2. Backend (`core.py`)
The backend contains the core business logic, FFmpeg integrations, and AI routing.
- **FFmpeg Orchestration:** Functions like `extract_clip()`, `stitch_clips()`, and `generate_contact_sheet()` wrap the `ffmpeg` subprocess commands, automatically handling resolution scaling (1080p), framerate normalization (25fps), and stream mapping.
- **AI Model Routing:** Functions like `generate_summary()` and `generate_storyboard()` manage the API calls to the local Ollama instance (port 11434). It supports mapping logic to swap between `llava`, `moondream`, or `deepseek-coder-v2`.
- **NLE Exports:** Functions like `generate_fcpxml()` and `generate_edl()` convert the Streamlit queue dictionary into standard XML or text formats for Final Cut Pro and DaVinci Resolve.

## 3. Intelligence Pipelines

### Vision Pipeline (`vision/vision_pipeline.py`)
Designed as a master orchestrator for visual intelligence (Phase 1/2 feature). It runs 6 concurrent modules (scene detection, face tracking, emotion, objects, text, motion) using OpenCV and machine learning models to generate a highly granular `vision_report.json`.

### Audio Pipeline (`audio/audio_pipeline.py`)
Designed to orchestrate audio intelligence. It extracts the `.wav` from the video and runs 5 parallel threads:
- **`transcriber.py`**: OpenAI Whisper.
- **`speaker_diarizer.py`**: Pyannote.audio (Requires `HF_TOKEN`).
- **`beat_detector.py`**: Librosa tempo/downbeat analysis.
- **`waveform_analyzer.py`**: RMS analysis for clipping, silence, and drops.
- **`noise_detector.py`**: Spectral flatness checks for background noise.

The audio orchestrator outputs an `audio_report.json` and a series of `Storyboard Hints` which are immediately parsed by the frontend to suggest edit points.
