# Video Compilation Toolkit

This project contains automated Python tools and AI-driven workflows used to process, extract, and compile documentary B-roll footage for the "Noor Women for Afghanistan" advocacy video. 

## Overview
The goal of this project is to take various news reports and raw drone footage, visually inspect them, and programmatically extract highly specific scenes (e.g., secret classrooms, Taliban patrols, girls studying). This toolkit now features a fully interactive **Streamlit Web GUI**.

## Core Technologies
*   **Python & Streamlit**: The frontend framework powering the local GUI.
*   **FFmpeg & ffprobe**: For lossless cutting, resolution/framerate normalization, and audio stripping.
*   **Pillow**: Used for image manipulation and contact sheet generation.
*   **Ollama (LLaVA)**: Local AI Vision model used for automatically describing and renaming video clips based on visual contents.
