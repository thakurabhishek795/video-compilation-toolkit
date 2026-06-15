import streamlit as st
import os
import core

st.set_page_config(page_title="Video Compilation Toolkit", page_icon="🎬", layout="wide")

st.title("🎬 Video Compilation Toolkit")
st.markdown("A GUI for extracting keyframes, generating contact sheets, and compiling B-roll footage.")

st.header("1. Media Library")
default_lib = "/Users/athakur/Downloads/taliban"
media_dir = st.text_input("Enter Media Library Directory Path:", value=default_lib)

if not os.path.isdir(media_dir):
    st.error(f"Directory does not exist: {media_dir}")
    st.stop()

videos = core.get_videos(media_dir)
if not videos:
    st.warning("No MP4 files found in the selected directory.")
else:
    st.success(f"Found {len(videos)} videos in the library.")
    with st.expander("View Available Videos"):
        for v in videos:
            st.text(v)

st.subheader("Rename Video")
ai_model = st.selectbox("Select AI Vision Model", ["llava", "deepseek-coder-v2", "bakllava", "moondream"])
col_A, col_B, col_C = st.columns([2, 2, 1])
with col_A:
    rename_sel = st.selectbox("Select video to rename", videos) if videos else st.empty()
    if st.button("✨ Auto-Suggest Name"):
        with st.spinner(f"Asking {ai_model}..."):
            try:
                suggested = core.suggest_video_name(media_dir, rename_sel, ai_model)
                st.session_state.suggested_name = suggested + ".mp4"
            except Exception as e:
                st.error(e)
with col_B:
    default_name = st.session_state.get("suggested_name", "")
    new_name_input = st.text_input("New descriptive name (e.g., drone_overview.mp4)", value=default_name)
with col_C:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Rename File"):
        if new_name_input and rename_sel:
            try:
                core.rename_video(media_dir, rename_sel, new_name_input)
                st.success(f"Renamed {rename_sel} to {new_name_input}")
                st.session_state.suggested_name = ""
                st.rerun()
            except Exception as e:
                st.error(f"Error renaming: {e}")

st.header("2. Keyframes & Contact Sheets")
if st.button("Generate Keyframes & Contact Sheets"):
    with st.spinner("Processing videos... This may take a moment."):
        core.generate_keyframes_and_sheets(media_dir)
        st.success("Keyframes and Contact Sheets generated!")

sheets = core.get_contact_sheets(media_dir)
if sheets:
    sheets_dir = os.path.join(media_dir, "contact_sheets")
    st.subheader("Contact Sheets Gallery")
    cols = st.columns(min(3, len(sheets)))
    for i, sheet in enumerate(sheets):
        with cols[i % len(cols)]:
            st.image(os.path.join(sheets_dir, sheet), caption=sheet, use_column_width=True)

st.header("3. Clip Compilation")
if "clips" not in st.session_state:
    st.session_state.clips = []

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
            "video": selected_vid,
            "start": start_time,
            "duration": duration,
            "out_name": out_name
        })
        st.success(f"Added {out_name}")

if st.session_state.clips:
    st.write("### Queued Clips")
    st.table(st.session_state.clips)
    
    if st.button("Clear Queue"):
        st.session_state.clips = []
        st.experimental_rerun()

    st.markdown("### Export")
    colA, colB = st.columns(2)
    with colA:
        if st.button("Export Individual Clips"):
            with st.spinner("Extracting..."):
                out_dir = core.export_individual_clips(media_dir, st.session_state.clips)
                st.success(f"Clips exported to {out_dir}")
                
    with colB:
        if st.button("Compile Unified B-Roll"):
            with st.spinner("Compiling..."):
                final_out = core.compile_unified_broll(media_dir, st.session_state.clips)
                st.success(f"Unified B-roll compiled to {final_out}")

st.header("4. AI Director (Storyboard)")
st.markdown("Paste your script below. The AI will analyze your text, review the contact sheets, and automatically suggest the best clips for each scene.")

script_text = st.text_area("Final Video Script", height=200, placeholder="Type or paste your script here...")
director_model = st.selectbox("Select AI Director Model", ["llava", "deepseek-coder-v2", "bakllava", "moondream"], key="director_model")

if st.button("🎬 Generate Storyboard"):
    if not script_text.strip():
        st.warning("Please enter a script first.")
    else:
        with st.spinner(f"The AI Director ({director_model}) is reading the script and reviewing contact sheets..."):
            try:
                storyboard = core.generate_storyboard(media_dir, script_text, director_model)
                st.session_state.storyboard = storyboard
                st.success("Storyboard generated successfully!")
            except Exception as e:
                st.error(str(e))

if "storyboard" in st.session_state and st.session_state.storyboard:
    st.markdown("---")
    st.subheader("Generated Storyboard")
    
    for scene in st.session_state.storyboard:
        with st.container():
            st.markdown(f"### Scene {scene.get('scene_number', '?')}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Script Segment:**")
                st.info(scene.get('script_segment', ''))
                st.markdown("**Visual Concept:**")
                st.write(scene.get('visual_concept', ''))
            with col2:
                clip = scene.get('suggested_clip', '')
                start_val = scene.get('start_time', '00:00:00')
                dur_val = scene.get('duration', '00:00:05')
                
                st.markdown("**Suggested Clip:**")
                st.success(f"{clip} (Start: {start_val}, Dur: {dur_val})")
                
                st.markdown("**Editing Tips:**")
                st.warning(scene.get('editing_tips', ''))
                
                if st.button(f"Add Scene {scene.get('scene_number', '?')} to Queue", key=f"add_scene_{scene.get('scene_number', '?')}"):
                    if "clips" not in st.session_state:
                        st.session_state.clips = []
                    
                    start_val = scene.get('start_time', '00:00:00')
                    dur_val = scene.get('duration', '00:00:05')
                    
                    st.session_state.clips.append({
                        "video": clip,
                        "start": start_val,
                        "duration": dur_val,
                        "out_name": f"scene_{scene.get('scene_number', '?')}.mp4"
                    })
                    st.rerun()
        st.markdown("---")

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
