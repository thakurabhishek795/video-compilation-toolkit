# Video Compilation Toolkit

The **Video Compilation Toolkit** is a Python-based Streamlit application designed to automate the process of organizing, logging, and compiling raw documentary B-roll footage. It features AI-driven storyboard generation and professional NLE (Non-Linear Editor) exporting capabilities.

## 📖 Documentation
To keep the repository clean and accessible for AI assistants, detailed documentation has been separated into the `docs/` folder:
- [Architecture Details](docs/ARCHITECTURE.md): Breakdown of the Frontend (`app.py`), Backend (`core.py`), and the Vision/Audio pipelines.
- [Project Roadmap](docs/ROADMAP.md): Current progress and upcoming feature phases.

## 🚀 Quickstart

### Prerequisites
- **Python 3.9+**
- **FFmpeg**: Must be installed and accessible in your system `PATH`.
- **Ollama**: Required for running local AI vision models (`moondream` or `llava`).

### Installation
```bash
# 1. Clone the repository
# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the Streamlit App
streamlit run app.py
```

## ✨ Core Features
1. **Contact Sheet Generator:** Automatically extracts frames from video files at intervals to create a visual grid.
2. **AI Video Summarizer:** Uses local vision models (via Ollama) to automatically describe video contents based on contact sheets.
3. **Interactive Editing Queue:** Stage cuts by specifying start time, duration, and output filename.
4. **Professional Exporting:** Export the queue directly to **Final Cut Pro (FCPXML)** or **DaVinci Resolve (EDL)**.
5. **AI Director (Storyboard Engine):** Paste a script, and the Hybrid AI (DeepSeek + Moondream) will automatically select the best clips and populate your timeline.
6. **Audio Intelligence:** Run 5-module deep audio analysis (transcription, beat detection, diarization) directly from the UI.
