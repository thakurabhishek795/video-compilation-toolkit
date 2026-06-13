import os
import subprocess

base_dir = "/Users/athakur/Downloads/taliban"
output_dir = os.path.join(base_dir, "individual_clips")
os.makedirs(output_dir, exist_ok=True)

clips_metadata = [
    (
        "12647598_1920_1080_50fps.mp4", 
        "00:00:00", 
        "00:00:04", 
        "clip_1_drone_overview.mp4"
    ),
    (
        "Women’s rights being rolled back in Afghanistan - BBC News-(720p50).mp4", 
        "00:04:14", 
        "00:00:04", 
        "clip_2_taliban_patrol.mp4"
    ),
    (
        "FRANCE 24 report： The Afghan girls defying Taliban bans to go to school • FRANCE 24 English-(1080p25).mp4", 
        "00:00:12", 
        "00:00:05", 
        "clip_3_secret_school_doorway.mp4"
    ),
    (
        "FRANCE 24 report： The Afghan girls defying Taliban bans to go to school • FRANCE 24 English-(1080p25).mp4", 
        "00:01:54", 
        "00:00:05", 
        "clip_4_writing_notebook.mp4"
    ),
    (
        "Women’s rights being rolled back in Afghanistan - BBC News-(720p50).mp4", 
        "00:01:55", 
        "00:00:05", 
        "clip_5_girl_silhouette_window.mp4"
    ),
    (
        "Afghanistan under the Taliban ｜ DW Documentary-(1080p25).mp4", 
        "00:11:56", 
        "00:00:06", 
        "clip_6_girl_rooftop_portrait.mp4"
    )
]

print("Extracting and normalizing individual clips...")

for idx, (filename, start, duration, out_name) in enumerate(clips_metadata):
    input_path = os.path.join(base_dir, filename)
    output_path = os.path.join(output_dir, out_name)
    temp_cut = os.path.join(output_dir, f"temp_{idx}.mp4")
    
    print(f"Processing: {out_name}")
    
    # Cut clip fast
    cut_cmd = [
        "ffmpeg", "-y", "-ss", start, "-i", input_path, "-t", duration,
        "-c", "copy", temp_cut
    ]
    subprocess.run(cut_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Normalize clip: scale/pad to 1920x1080, 25fps, strip audio (-an), yuv420p
    norm_cmd = [
        "ffmpeg", "-y", "-i", temp_cut,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-r", "25", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path
    ]
    subprocess.run(norm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Clean up temp cut
    if os.path.exists(temp_cut):
        os.remove(temp_cut)

print(f"Success! Individual clips saved in: {output_dir}")
