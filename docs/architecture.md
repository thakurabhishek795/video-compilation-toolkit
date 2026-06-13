# System Architecture

The toolkit features a decoupled architecture allowing both human and AI interaction:
*   **Streamlit Frontend (Port 8501)**: A GUI for human editors.
*   **FastAPI Backend (Port 8000)**: A REST API layer designed for Agentic AI orchestration.
*   **Core Logic (`core.py`)**: Shared Python module containing all FFmpeg processing.

The core video processing pipeline operates in four distinct stages:

## 1. Keyframe Extraction
Raw MP4 files are processed using FFmpeg to extract low-resolution JPEG thumbnails at fixed intervals (e.g., every 10 or 30 seconds).

## 2. Visual Analysis (Contact Sheets)
The extracted frames are stitched together into large grid images ("contact sheets") using Python's Pillow library. This allows an AI agent or human editor to visually scan the entire contents of a video in a single glance.

### 2a. Local AI Vision (Ollama)
The toolkit integrates directly with **Ollama** running the **LLaVA** multimodal model. Contact sheets are routed to `localhost:11434` where the local AI automatically describes the scenes and suggests descriptive filenames for the clips.

## 3. Segmentation & Normalization
Specific timestamps are identified. FFmpeg is used to:
*   Cut the segments losslessly (`-c copy`).
*   Scale and pad the video to a uniform 1920x1080 resolution.
*   Lock the frame rate to 25 FPS.
*   Strip the original audio tracks (`-an`).

## 4. Compilation
The normalized clips are either exported as individual files for a non-linear editor (NLE) or concatenated into a single seamless B-roll compilation using FFmpeg's `concat` demuxer.
