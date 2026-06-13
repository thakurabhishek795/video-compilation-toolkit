# Implementation Plan: Local AI Vision Integration

The goal is to integrate a **locally run AI Vision model** into the toolkit. This AI will be able to "look" at the contact sheets we generate and automatically suggest descriptive names (e.g., `girls_in_classroom`, `drone_city_view`) for the video clips, eliminating the need for manual renaming!

## User Review Required

> [!IMPORTANT]
> **Tech Stack: Ollama (LLaVA)**
> To run AI vision locally on a Mac smoothly, I propose using **[Ollama](https://ollama.com/)** running the **LLaVA** (Large Language-and-Vision Assistant) model. 
> *   **Why Ollama?** It automatically utilizes your Mac's hardware acceleration (Metal/Apple Silicon) for fast inference. It keeps our Python virtual environment lightweight.
> *   **Alternative**: We could install PyTorch directly in the virtual environment and use a tiny model like `Moondream2`, but it requires massive 2GB+ downloads and can be significantly slower.

## Open Questions

> [!WARNING]
> 1. **Ollama Setup:** Are you comfortable installing Ollama on your Mac (if you haven't already)? I can provide the single terminal command to do it.
> 2. **Workflow:** Would you prefer the AI to automatically rename the files behind the scenes, or would you prefer a magic ✨ **"Auto-Suggest Name"** button in the UI that fills in the text box for your final approval? *(I recommend the UI button approach for safety)*.

## Proposed Changes

### 1. System Requirements
*   Ensure Ollama is running.
*   Download the vision model: `ollama pull llava`.

### 2. Core Logic (`core.py`)
*   Add a new function `suggest_video_name(media_dir, video_name)` that finds the video's contact sheet image.
*   Encode the image to base64 and send it to the local Ollama API (`http://localhost:11434/api/generate`) with a specific prompt: *"Analyze these video keyframes. Describe the main subject in 2 to 4 words. Use underscores instead of spaces. Do not include file extensions. Example: afghan_girls_studying"*

### 3. Update API Layer (`api.py`)
*   Create a `POST /library/ai-suggest` endpoint that accepts a video filename and returns the AI's suggested name.

### 4. Update Streamlit GUI (`app.py`)
*   In the existing "Rename Video" section, add a ✨ **"Suggest with AI"** button next to the video selector.
*   When clicked, it will ping the local AI, and populate the "New descriptive name" input box with the result, allowing you to quickly review and click Rename.

## Verification Plan
1. Wait for your approval on the Ollama approach.
2. Write the integration code across `core.py`, `api.py`, and `app.py`.
3. Restart the FastAPI server.
4. Test the pipeline by clicking the Auto-Suggest button on one of the Afghanistan B-roll contact sheets.
