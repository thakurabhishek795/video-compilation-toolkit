# Video Compilation Toolkit - Roadmap

This document outlines future features and implementations that can be integrated into our application to enhance its capabilities. It is maintained here so that AI agents understand the trajectory of the project.

## 🎯 Strategic Phases

### Phase 1 (Quick Wins) 🟢
├── Audio transcription (Whisper) **[IMPLEMENTED in `audio/`]**
├── Scene change detection (OpenCV) **[IMPLEMENTED in `vision/`]**
├── Stock footage search API
├── Confidence threshold slider
└── SRT/caption export

### Phase 2 (Core Value) 🟡
├── NLE export (FCPXML/EDL) **[IMPLEMENTED]**
├── Interactive timeline viewer
├── Speaker diarization **[IMPLEMENTED in `audio/`]**
├── Human feedback loop
└── Genre-specific modes

### Phase 3 (Differentiation) 🔴
├── B-roll auto-generation (LTX-2)
├── Engagement prediction
└── Queue system for scale

---

## 🚀 Planned Integrations

1. **Clip Cutter**
   - **Description**: Use AI to automatically scan long videos and detect/extract "viral-worthy" moments or shorts based on visual and audio context.

2. **Auto Caption**
   - **Description**: Utilize local Whisper models to transcribe audio, an LLM to correct grammar/context, and FFmpeg to burn the subtitles directly into the video.

3. **Auto Tag**
   - **Description**: Automatically generate optimized YouTube/social media titles, descriptions, and tags based on analyzing the video's content and keyframes.

4. **Thumbnail Candidates**
   - **Description**: Extract the best, most visually appealing frames from the video to use as thumbnails, and generate text ideas for the thumbnail captions.

5. **Format Conversion**
   - **Description**: Convert video files between different formats (e.g., from `.avi` or `.mkv` to `.mp4`) directly from the UI.

6. **Video Combine / Append**
   - **Description**: Merge two identically sized videos sequentially (stitching the second video directly onto the end of the first).

7. **Background Music to Voiceover Mixing**
   - **Description**: Automatically mix a background music track underneath a primary voiceover audio file, applying smart ducking (lowering music volume when speaking).
