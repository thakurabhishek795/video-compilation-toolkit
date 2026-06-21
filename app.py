import streamlit as st
import os
import core
import safe_fcpxml

st.set_page_config(page_title="Video Compilation Toolkit", page_icon="🎬", layout="wide")

st.title("🎬 Video Compilation Toolkit")
st.markdown("A GUI for extracting keyframes, generating contact sheets, and compiling B-roll footage.")

st.header("1. Media Library")
default_lib = "/Users/athakur/Downloads/taliban"
media_dir = st.text_input("Enter Media Library Directory Path:", value=default_lib)

if not os.path.isdir(media_dir):
    st.error(f"Directory does not exist: {media_dir}")
    st.stop()

videos = core.get_media_files(media_dir)
if videos:
    st.sidebar.markdown(f"**Found {len(videos)} media files**")
else:
    st.warning("No MP4 files found in the selected directory.")
    
if videos:
    st.success(f"Found {len(videos)} videos in the library.")
    with st.expander("View Available Videos"):
        for v in videos:
            st.text(v)

st.header("2. Keyframes & Contact Sheets")
if st.button("Generate Keyframes & Contact Sheets"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    def keyframe_progress(pct, msg):
        progress_bar.progress(pct)
        status_text.text(msg)
        
    core.generate_keyframes_and_sheets(media_dir, progress_callback=keyframe_progress)
    st.success("Keyframes and Contact Sheets generated!")

sheets = core.get_contact_sheets(media_dir)
if sheets:
    sheets_dir = os.path.join(media_dir, "contact_sheets")
    st.subheader("Contact Sheets Gallery")
    cols = st.columns(min(3, len(sheets)))
    for i, sheet in enumerate(sheets):
        with cols[i % len(cols)]:
            st.image(os.path.join(sheets_dir, sheet), caption=sheet, use_container_width=True)

st.subheader("Batch Media Rename")
ai_model = st.selectbox("Select AI Vision Model", ["llava", "moondream"])

rename_sel = st.multiselect("Select videos to rename", videos) if videos else []

if "batch_suggestions" not in st.session_state:
    st.session_state.batch_suggestions = {}

if st.button("✨ Auto-Suggest Names"):
    if rename_sel:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        import re
        max_num = 0
        for v in videos:
            match = re.match(r"^video_(\d+)_", v)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
                    
        current_seq = max_num + 1
        
        for i, video_file in enumerate(rename_sel):
            status_text.text(f"Processing {video_file} ({i+1}/{len(rename_sel)})...")
            try:
                suggested = core.suggest_video_name(media_dir, video_file, ai_model)
                prefix = f"video_{current_seq:02d}_"
                st.session_state.batch_suggestions[video_file] = prefix + suggested + ".mp4"
                current_seq += 1
            except Exception as e:
                st.error(f"Error suggesting name for {video_file}: {e}")
            progress_bar.progress((i + 1) / len(rename_sel))
            
        status_text.text("Finished generating suggestions!")
    else:
        st.warning("Please select at least one video to rename.")

# Dictionary to hold the final input values before renaming
new_names = {}

if rename_sel:
    st.markdown("### Review & Rename")
    for video_file in rename_sel:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.text(video_file)
        with col2:
            default_val = st.session_state.batch_suggestions.get(video_file, "")
            new_names[video_file] = st.text_input(f"New name for {video_file}", value=default_val, key=f"rename_input_{video_file}", label_visibility="collapsed")
            
    if st.button("Rename All Selected"):
        mapping = {}
        for video_file, new_name in new_names.items():
            if new_name and new_name != video_file:
                mapping[video_file] = new_name
                
        if mapping:
            with st.spinner("Safely renaming files..."):
                try:
                    manifest_path = core.batch_rename_videos_safely(media_dir, mapping)
                    st.success(f"Renamed {len(mapping)} files successfully!")
                    st.info(f"Audit Trail Saved: {manifest_path}")
                    for video_file in mapping:
                        if video_file in st.session_state.batch_suggestions:
                            del st.session_state.batch_suggestions[video_file]
                    import time
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Batch Rename Failed: {e}")

st.header("3. Clip Compilation")
if "clips" not in st.session_state:
    st.session_state.clips = []

def calc_end_time(start_str, dur_str):
    try:
        h1, m1, s1 = map(int, start_str.split(":"))
        h2, m2, s2 = map(int, dur_str.split(":"))
        total_sec = (h1*3600 + m1*60 + s1) + (h2*3600 + m2*60 + s2)
        return f"{total_sec//3600:02d}:{(total_sec%3600)//60:02d}:{total_sec%60:02d}"
    except Exception:
        return "Unknown"

with st.form("add_clip_form"):
    col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
    with col1:
        selected_vid = st.selectbox("Select Video", videos) if videos else st.selectbox("Select Video", ["None"])
    with col2:
        start_time = st.text_input("Start Time", value="00:00:00")
    with col3:
        duration = st.text_input("Duration", value="00:00:05")
    with col4:
        out_name = st.text_input("Output Name", value="clip.mp4")
    
    submitted = st.form_submit_button("Add Clip")
    if submitted and selected_vid != "None":
        st.session_state.clips.append({
            "File Name": selected_vid,
            "Start Time": start_time,
            "Duration": duration,
            "End Time": calc_end_time(start_time, duration),
            "Output Name": out_name,
            "Caption": ""
        })
        st.success(f"Added {out_name}")

if st.session_state.clips:
    st.write("### Queued Clips")
    st.info("💡 Edit the table below to tweak durations or captions, or use the toolbar to add/delete clips before compiling.")
    
    # st.data_editor creates an interactive table
    edited_clips = st.data_editor(
        st.session_state.clips,
        num_rows="dynamic",
        use_container_width=True,
        key="timeline_editor"
    )
    st.session_state.clips = edited_clips
    
    if st.button("Clear Queue"):
        st.session_state.clips = []
        st.rerun()

    st.markdown("### Export")
    colA, colB = st.columns(2)
    with colA:
        if st.button("Export Individual Clips"):
            with st.spinner("Extracting..."):
                out_dir = core.export_individual_clips(media_dir, st.session_state.clips)
                st.success(f"Clips exported to {out_dir}")
                
    with colB:
        burn_captions = st.checkbox("🔥 Burn-in AI Captions", value=False, help="Render the AI-generated captions physically onto the video with cinematic formatting.")
        if st.button("Compile Unified B-Roll"):
            with st.spinner("Compiling..."):
                try:
                    final_out = core.compile_unified_broll(media_dir, st.session_state.clips, burn_captions=burn_captions)
                    st.success(f"Unified B-roll compiled to {final_out}")
                    
                    # QA Verification
                    with st.spinner("Running QA Verification..."):
                        qa_report = core.verify_compilation(final_out)
                    
                    st.markdown("### 📊 QA Verification Report")
                    if qa_report.get("Status") == "Passed":
                        st.success("Verification Passed")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Duration", f"{qa_report.get('Duration (sec)')}s")
                        c2.metric("Resolution", qa_report.get('Resolution'))
                        c3.metric("FPS", qa_report.get('FPS'))
                        c4.metric("Codec", qa_report.get('Codec'))
                    else:
                        st.error(f"Verification Failed: {qa_report.get('Status')}")
                        
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    st.error(f"FFMPEG Error: {str(e)}")
                    
        fcpxml_data = core.generate_fcpxml(media_dir, st.session_state.clips)
        st.download_button(
            label="📤 Export to Final Cut / DaVinci (FCPXML)",
            data=fcpxml_data,
            file_name="unified_broll_storyboard.fcpxml",
            mime="application/xml",
        )
        
        edl_data = core.generate_edl(st.session_state.clips)
        st.download_button(
            label="📤 Export to DaVinci Resolve (EDL)",
            data=edl_data,
            file_name="unified_broll_storyboard.edl",
            mime="text/plain",
        )

st.header("4. AI Director (Storyboard & Audio Intelligence)")
st.markdown("Generate a storyboard from a script, or run deep audio analysis on your media files.")

tab_script, tab_audio = st.tabs(["📝 Script to Storyboard", "🎧 Audio Intelligence"])

with tab_script:
    script_text = st.text_area("Final Video Script", height=200, placeholder="Type or paste your script here...")
    model_mapping = {
        "Hybrid AI Director (Moondream + Deepseek)": "deepseek-coder-v2",
        "LLaVA (Standard)": "llava",
        "BakLLaVA (Standard)": "bakllava"
    }
    director_display = st.selectbox("Select AI Director Model", list(model_mapping.keys()), key="director_model")
    director_model = model_mapping[director_display]
    
    if st.button("🎬 Generate Storyboard"):
        if not media_dir or not os.path.exists(media_dir):
            st.error("Please enter a valid directory.")
        elif not script_text.strip():
            st.error("Please enter a script.")
        else:
            st.session_state.clips = []
            status_text = st.empty()
            stream_container = st.empty()
            
            def stream_update(text):
                if text.startswith("Visual analysis:"):
                    status_text.text(text)
                else:
                    status_text.text("AI Director is generating storyboard...")
                    stream_container.markdown(f"```json\n{text}\n```")
                    
            try:
                storyboard = core.generate_storyboard(media_dir, script_text, director_model, stream_callback=stream_update)
                status_text.text("Finished!")
                st.session_state.storyboard = storyboard
                st.success("Storyboard generated successfully!")
            except Exception as e:
                st.error(str(e))

with tab_audio:
    if "last_audio_summary" in st.session_state:
        last_audio = st.session_state.last_audio_summary
        st.subheader("Latest Audio Intelligence Summary")
        st.write(f"**Analyzed File:** `{last_audio.get('input_file', 'Unknown')}`")
        
        summary = last_audio.get("summary", {})
        
        # Format the summary into clean metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Quality Score", f"{summary.get('audio_quality_score', 0):.2f}/10")
        col2.metric("Total Speakers", summary.get("total_speakers", 0))
        col3.metric("Speech Coverage", f"{summary.get('speech_coverage_pct', 0):.1f}%")
        col4.metric("Total Words", summary.get("total_words", 0))
        
        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Music Detected", "Yes" if summary.get("music_present") else "No")
        col6.metric("Tempo (BPM)", f"{summary.get('tempo_bpm', 0):.1f}" if summary.get("music_present") else "N/A")
        col7.metric("Silence Regions", summary.get("silence_regions", 0))
        col8.metric("Noise Flags", summary.get("noise_flags", 0))
        
        st.divider()

    if media_dir and os.path.exists(media_dir):
        media_files = [f for f in os.listdir(media_dir) if f.endswith(('.mp4', '.mov', '.wav', '.mp3'))]
        if media_files:
            audio_file = st.selectbox("Select Media File to Analyze", media_files)
            if st.button("🎧 Run Audio Intelligence Pipeline"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def audio_progress(pct, msg):
                    progress_bar.progress(pct)
                    status_text.text(msg)
                    
                status_text.text(f"Running 5-module Audio Intelligence on {audio_file}... This may take a few minutes.")
                try:
                    report = core.run_audio_pipeline(media_dir, audio_file, progress_callback=audio_progress)
                    status_text.text("Finished!")
                    summary = report.get("summary", {})
                    quality_score = summary.get("audio_quality_score", 0.0)
                    st.success(f"Audio Intelligence Complete! Quality Score: {quality_score:.2f}")

                    import json
                    import time

                    summary_dir = os.path.join(media_dir, "audio_reports")
                    os.makedirs(summary_dir, exist_ok=True)
                    summary_path = os.path.join(
                        summary_dir,
                        f"audio_summary_{os.path.splitext(audio_file)[0]}_{int(time.time())}.json"
                    )
                    summary_payload = {
                        "input_file": audio_file,
                        "input_path": os.path.join(media_dir, audio_file),
                        "summary": summary,
                        "duration_sec": report.get("duration_sec", 0),
                        "audio_report_path": os.path.join(summary_dir, "audio_report.json"),
                    }
                    with open(summary_path, "w") as f:
                        json.dump(summary_payload, f, indent=2)

                    st.session_state.last_audio_summary = {
                        "input_file": audio_file,
                        "summary": summary,
                        "summary_path": summary_path,
                    }
                    st.subheader("Audio Intelligence Summary")
                    st.write(f"**Input:** {audio_file}")
                    st.write(f"**Summary file:** {summary_path}")
                    st.json(summary)
                    
                    # Fetch the generated hints which are saved to output_dir
                    hints_path = os.path.join(media_dir, "audio_reports", "audio_storyboard_hints.json")
                    if os.path.exists(hints_path):
                        with open(hints_path, "r") as f:
                            audio_hints = json.load(f)
                        # Convert to format compatible with storyboard UI
                        st.session_state.storyboard = {
                            "summary": {
                                "total_suggestions": len(audio_hints),
                                "high_priority": len([h for h in audio_hints if h.get("priority") == "high"]),
                                "medium_priority": len([h for h in audio_hints if h.get("priority") == "medium"]),
                                "estimated_edit_time_min": len(audio_hints) * 2
                            },
                            "storyboard": audio_hints
                        }
                        st.rerun()
                except Exception as e:
                    st.error(f"Audio Pipeline failed: {str(e)}")
        else:
            st.warning("No valid media files found in directory.")
    else:
        st.warning("Please enter a valid media directory above.")

if "storyboard" in st.session_state and st.session_state.storyboard:
    sb_data = st.session_state.storyboard
    if isinstance(sb_data, dict) and "storyboard" in sb_data:
        st.markdown("---")
        st.subheader("Storyboard Summary")
        
        # Display Summary block
        summary = sb_data.get("summary", {})
        colA, colB, colC, colD = st.columns(4)
        colA.metric("Total Suggestions", summary.get("total_suggestions", 0))
        colB.metric("High Priority", summary.get("high_priority", 0))
        colC.metric("Medium Priority", summary.get("medium_priority", 0))
        colD.metric("Est. Edit Time", f"{summary.get('estimated_edit_time_min', 0)} min")
        
        st.markdown("---")
        st.subheader("Event Timeline")
        
        events = sb_data.get("storyboard", [])
        for i, event in enumerate(events):
            action = event.get("action", "unknown")
            timestamp = event.get("timestamp", "0:00")
            confidence = event.get("confidence", 0.0)
            priority = event.get("priority", "medium")
            
            with st.container():
                st.markdown(f"### {timestamp} - {action.upper()}")
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Description:** {event.get('description', '')}")
                    if event.get("subtype") and event.get("subtype") != "none":
                        st.write(f"**Subtype:** {event.get('subtype')}")
                
                with col2:
                    st.write(f"**Confidence:** {confidence}")
                    st.write(f"**Priority:** {priority}")
                    
                if action == "insert_broll":
                    clip = event.get('suggested_clip', '')
                    dur_val = event.get('duration_suggestion_sec', 5.0)
                    if dur_val is None: dur_val = 5.0
                    source_start = str(event.get('source_start_timestamp', '00:00:00'))
                    if ":" in source_start:
                        start_str = source_start
                    else:
                        try:
                            sec = float(source_start)
                            start_str = f"{int(sec)//3600:02d}:{(int(sec)%3600)//60:02d}:{int(sec)%60:02d}"
                        except:
                            start_str = "00:00:00"
                            
                    dur_str = f"{int(dur_val)//3600:02d}:{(int(dur_val)%3600)//60:02d}:{int(dur_val)%60:02d}"
                    
                    if st.button(f"Add Clip at {timestamp} to Queue", key=f"add_clip_{i}"):
                        if "clips" not in st.session_state:
                            st.session_state.clips = []
                        st.session_state.clips.append({
                            "File Name": clip,
                            "Start Time": start_str,
                            "Duration": dur_str,
                            "End Time": calc_end_time(start_str, dur_str),
                            "Output Name": f"clip_{len(st.session_state.clips)}.mp4",
                            "Caption": event.get("caption", "")
                        })
                        st.rerun()
                elif action == "music_change":
                    st.info("🎵 Music Change Suggested here.")
                elif action == "text_overlay":
                    st.warning("📝 Text Overlay Suggested here.")
                elif action == "transition":
                    st.info("🔄 Transition Suggested here.")
                    
            st.markdown("---")
    else:
        st.error("The generated storyboard is in an older format. Please generate a new storyboard.")

st.header("5. Video Toolkit")
st.markdown("A collection of utilities inspired by VideoProcessToolkit natively powered by FFmpeg.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Reverse", "Resize", "Downsample", "Compose (PiP)", "AI Assistant", "AI Music"])

with tab1:
    st.subheader("Reverse Video")
    rev_vid = st.selectbox("Select Video", videos, key="rev_vid") if videos else None
    rev_out = st.text_input("Output Name", value="reversed.mp4", key="rev_out")
    if st.button("Reverse Video") and rev_vid:
        with st.spinner("Reversing..."):
            try:
                core.reverse_video(os.path.join(media_dir, rev_vid), os.path.join(media_dir, rev_out))
                st.success(f"Saved to {rev_out}")
            except Exception as e:
                st.error(e)

with tab2:
    st.subheader("Resize Video")
    res_vid = st.selectbox("Select Video", videos, key="res_vid") if videos else None
    res_rate = st.slider("Resize Rate", min_value=0.1, max_value=2.0, value=0.5, step=0.1)
    res_out = st.text_input("Output Name", value="resized.mp4", key="res_out")
    if st.button("Resize Video") and res_vid:
        with st.spinner("Resizing..."):
            try:
                core.resize_video(os.path.join(media_dir, res_vid), res_rate, os.path.join(media_dir, res_out))
                st.success(f"Saved to {res_out}")
            except Exception as e:
                st.error(e)

with tab3:
    st.subheader("Downsample Video")
    ds_vid = st.selectbox("Select Video", videos, key="ds_vid") if videos else None
    ds_fps = st.number_input("Target FPS", min_value=1, max_value=60, value=15)
    ds_out = st.text_input("Output Name", value="downsampled.mp4", key="ds_out")
    if st.button("Downsample Video") and ds_vid:
        with st.spinner("Downsampling..."):
            try:
                core.downsample_video(os.path.join(media_dir, ds_vid), ds_fps, os.path.join(media_dir, ds_out))
                st.success(f"Saved to {ds_out}")
            except Exception as e:
                st.error(e)

with tab4:
    st.subheader("Compose (Picture-in-Picture)")
    main_vid = st.selectbox("Main Video", videos, key="main_vid") if videos else None
    sub_vid = st.selectbox("Sub Video (Overlay)", videos, key="sub_vid") if videos else None
    comp_out = st.text_input("Output Name", value="composed.mp4", key="comp_out")
    if st.button("Compose Videos") and main_vid and sub_vid:
        with st.spinner("Composing..."):
            try:
                core.compose_video(os.path.join(media_dir, main_vid), os.path.join(media_dir, sub_vid), os.path.join(media_dir, comp_out))
                st.success(f"Saved to {comp_out}")
            except Exception as e:
                st.error(e)

with tab5:
    st.subheader("🤖 AI FFmpeg Assistant")
    st.markdown("Describe the edit you want to make in natural language. The AI will generate and run the FFmpeg command for you!")
    ai_vid = st.selectbox("Select Video", videos, key="ai_vid") if videos else None
    ai_model = st.selectbox("Select AI Model", ["llava", "deepseek-coder-v2", "bakllava", "moondream"], key="ai_model_toolkit")
    ai_instruction = st.text_area("Instruction (e.g., 'Make it black and white and speed it up 2x')", key="ai_instruction")
    ai_out = st.text_input("Output Name", value="ai_edited.mp4", key="ai_out")
    
    if st.button("✨ Run AI Assistant") and ai_vid and ai_instruction:
        with st.spinner(f"Asking {ai_model} to generate and run FFmpeg command..."):
            try:
                command = core.ai_ffmpeg_assistant(media_dir, ai_instruction, ai_vid, ai_out, ai_model)
                st.success(f"Generated Command:\n```bash\n{command}\n```")
                st.success(f"Successfully processed and saved to {ai_out}")
            except Exception as e:
                st.error(str(e))

with tab6:
    st.subheader("🎵 AI Music Generator")
    st.markdown("Generate background music using the ACE-Step API.")
    ace_api_key = st.text_input("ACE-Step API Key", type="password", value="a64c8deb3c624baabd09c9b541b89c14", key="ace_api_key")
    music_prompt = st.text_area("Prompt (e.g., 'Upbeat corporate tech background')", key="music_prompt")
    music_duration = st.slider("Duration (seconds)", min_value=10, max_value=120, value=30, step=10, key="music_duration")
    music_out = st.text_input("Output Name", value="bg_music.mp3", key="music_out")
    
    if st.button("🎶 Generate Music") and music_prompt and ace_api_key:
        with st.spinner("Generating music with ACE-Step XL Turbo..."):
            try:
                out_path = core.generate_music(music_prompt, music_duration, ace_api_key, music_out, media_dir)
                st.success(f"Successfully generated and saved to {music_out}")
                st.audio(out_path)
            except Exception as e:
                st.error(str(e))

# --- Safe FCPXML workflow added by Codex ---
st.header("6. Safe Final Cut XML + Batch Rename")
st.markdown(
    "Crash-safe workflow proven with the Noor Women project: still photos are "
    "converted into short MP4 proxies, then the XML references only video media."
)

try:
    safe_media_files = safe_fcpxml.media_files(media_dir)
except Exception as e:
    safe_media_files = []
    st.error(str(e))

if not safe_media_files:
    st.info("No image/video media found for the safe XML workflow.")
else:
    st.success(f"Safe workflow sees {len(safe_media_files)} image/video files.")

    st.subheader("Batch Rename")
    rename_selection = st.multiselect(
        "Select files to rename",
        safe_media_files,
        default=safe_media_files[: min(10, len(safe_media_files))],
        key="safe_rename_selection",
    )
    rename_rows = []
    for selected_name in rename_selection:
        suggested = os.path.splitext(selected_name)[0].lower().replace(" ", "_")
        new_stem = st.text_input(
            f"New name for {selected_name}",
            value=suggested,
            key=f"safe_rename_{selected_name}",
        )
        rename_rows.append({"File Name": selected_name, "New Name": new_stem})

    if st.button("Rename Selected Media", key="safe_batch_rename"):
        try:
            manifest = safe_fcpxml.rename_media_batch(media_dir, rename_rows, prefix=True)
            st.success(f"Rename manifest created: {manifest}")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    st.subheader("Final Cut Safe XML")
    timeline_selection = st.multiselect(
        "Select timeline files in order",
        safe_media_files,
        default=safe_media_files[: min(20, len(safe_media_files))],
        key="safe_timeline_selection",
    )
    default_duration = st.number_input(
        "Default clip duration, seconds",
        min_value=1.0,
        max_value=30.0,
        value=5.0,
        step=0.5,
        key="safe_duration",
    )
    safe_project_name = st.text_input(
        "Project name",
        value="Noor Women Safe Source Timeline",
        key="safe_project_name",
    )
    timeline_rows = [
        {
            "File Name": filename,
            "Start Time": "00:00:00",
            "Duration": f"00:00:{int(default_duration):02d}",
            "Output Name": filename,
        }
        for filename in timeline_selection
    ]

    if st.button("Create Crash-Safe Final Cut XML", key="safe_fcpxml_export"):
        try:
            xml_path, manifest_path = safe_fcpxml.generate_final_cut_safe_xml(
                media_dir,
                timeline_rows,
                project_name=safe_project_name,
            )
            st.success(f"Final Cut XML created: {xml_path}")
            st.info(f"Timeline manifest: {manifest_path}")
            with open(xml_path, "rb") as f:
                st.download_button(
                    "Download Safe FCPXML",
                    data=f,
                    file_name=os.path.basename(xml_path),
                    mime="application/xml",
                )
        except Exception as e:
            st.error(str(e))
