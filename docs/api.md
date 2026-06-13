# REST API Documentation

The Video Compilation Toolkit exposes a FastAPI backend running on port 8000. It provides OpenAPI/Swagger documentation out of the box.

## Automatic Swagger UI
AI agents and humans can browse the interactive API schema by navigating to:
**[http://localhost:8000/docs](http://localhost:8000/docs)**

## Endpoints

### 1. `GET /library/videos`
Returns a list of all `.mp4` files in the specified library.
*   **Query Params**: `media_dir` (string)
*   **Response**: `{"media_dir": "...", "videos": ["clip1.mp4", ...]}`

### 2. `POST /library/rename`
Renames a video file in the library to a new descriptive name.
*   **Body (JSON)**: 
    ```json
    {
      "media_dir": "/Users/athakur/Downloads/taliban",
      "old_name": "12647598_1920_1080_50fps.mp4",
      "new_name": "drone_overview.mp4"
    }
    ```
*   **Response**: `{"message": "Video renamed successfully.", "new_name": "drone_overview.mp4"}`

### 3. `POST /library/ai-suggest`
Sends the video's contact sheet to the local Ollama LLaVA model to automatically suggest a descriptive filename.
*   **Body (JSON)**: `{"media_dir": "...", "video_name": "..."}`
*   **Response**: `{"message": "...", "suggested_name": "drone_city_view"}`

### 4. `POST /director/storyboard`
Acts as an AI film director. Analyzes a script alongside all contact sheets in the media library and outputs a structured JSON storyboard recommending specific clips for each scene.
*   **Body (JSON)**: `{"media_dir": "...", "script": "...", "model": "llava"}`
*   **Response**: `{"message": "...", "storyboard": [...]}`

### 5. `POST /library/keyframes`
Triggers the extraction of keyframes and generates visual contact sheets.
*   **Query Params**: `media_dir` (string)
*   **Response**: `{"message": "...", "results": [...]}`

### 6. `POST /export/clips`
Extracts defined video segments into individual, normalized silent MP4 files.
*   **Body (JSON)**: 
    ```json
    {
      "media_dir": "/Users/athakur/Downloads/taliban",
      "clips": [
        {"video": "raw.mp4", "start": "00:00:10", "duration": "00:00:05", "out_name": "scene1.mp4"}
      ]
    }
    ```

### 7. `POST /export/compile`
Extracts and seamlessly merges defined video segments into a single `final_broll_compilation.mp4`.
*   **Body (JSON)**: Same as `/export/clips`.
*   **Response**: `{"message": "B-roll compiled successfully.", "file": "path/to/final.mp4"}`
