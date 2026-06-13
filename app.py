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
