# Video Compilation Toolkit

An end-to-end Python/Streamlit application that leverages local and cloud-based AI models to automate video editing workflows—from intelligent video discovery and keyframe extraction to AI-powered storyboarding, audio intelligence, and NLE export.

## Features

- **Media Library Browser:** Instantly scans and processes local directories for videos and images.
- **AI-Powered File Renaming:** Automatically rename messy file names (like `WhatsApp Video...`) into descriptive, safe names using local vision models.
- **Human-in-the-Loop Storyboarding:** Generate dynamic JSON storyboards using a hybrid Moondream (Vision) + DeepSeek-Coder-V2 (Logic) architecture, or standard LLaVA. 
- **Interactive Timeline Editor:** Interactively drag, drop, and edit captions and clip durations before final rendering.
- **Cinematic Compilation Engine:** Automatically scales, pads (with blurred backgrounds for vertical videos), and compiles unified B-roll via FFmpeg.
- **Burn-in AI Captions:** Generates poetic beats from your script and burns them directly onto the final video using FFmpeg `drawtext`.
- **Audio Intelligence Pipeline:** Extracts transcripts via Whisper, tempo/beats via Librosa, and speaker diarization via Pyannote to recommend precise audio-synced cuts.
- **NLE Export:** Export your timeline directly to FCPXML (Final Cut Pro / DaVinci Resolve) and EDL.
- **Video Utilities:** Reverse, resize, downsample, and Picture-in-Picture directly from the UI natively powered by FFmpeg.
- **AI FFmpeg Assistant:** Chat with an AI assistant that writes and executes complex FFmpeg terminal commands for you.
- **AI Music Generator:** Integrates with the ACE-Step API to synthesize custom background music.

## Architecture

```text
├── Frontend (app.py)          <-- Streamlit UI, Interactive Timeline, Media Browser
├── Core Backend (core.py)     <-- FFmpeg Orchestration, Storyboard Generation, NLE Export
├── Audio Pipeline (audio/)    <-- Transcription, Diarization, Beat Detection
└── Vision Pipeline (vision/)  <-- Scene Detection, Face/Emotion Tracking (In Progress)
```

**Key Integration Points:**
- `app.py` acts as the master state manager (`st.session_state`), handling clip queues.
- Local AI routing connects to an Ollama server running on `localhost:11434`.

## Installation

### 1. Prerequisites
- **Python 3.9+**
- **FFmpeg**: Must be installed and accessible in your system `$PATH`. Must be compiled with `--enable-libfreetype` and `--enable-libfontconfig` for burned-in captions to work.
- **Ollama**: Must be installed and running locally (`ollama serve`). 
  - Required Models: `ollama run moondream`, `ollama run deepseek-coder-v2`, `ollama run llava`.

### 2. Install Dependencies
Clone the repository and install the required Python packages:

```bash
git clone https://github.com/thakurabhishek795/video-compilation-toolkit.git
cd video-compilation-toolkit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Setup Secrets
For the AI Music Generator to work, you must provide an ACE-Step API key in Streamlit secrets.
Create a file at `.streamlit/secrets.toml`:
```toml
ace_step_api_key = "your_api_key_here"
```

## Usage

Start the Streamlit application:
```bash
streamlit run app.py
```

## Known Issues & Limitations
- **Vision Pipeline**: The advanced vision pipeline orchestrator is currently stubbed out (OpenCV/YOLO logic in progress).
- **Audio Decoding**: FFmpeg may occasionally extract malformed `.wav` files if the source video has no audio track, causing the Audio Pipeline to throw an `EOFError`.
- **System Fonts**: The Burn-in Captions feature relies on FFmpeg finding a default system font. If it fails, the render will crash.

---
*Built for automating complex documentary, vlog, and short-form video editing pipelines.*
