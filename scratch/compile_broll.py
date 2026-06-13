import os
import subprocess

base_dir = "/Users/athakur/Downloads/taliban"
temp_dir = os.path.join(base_dir, "temp_clips")
os.makedirs(temp_dir, exist_ok=True)

# Define the edits: (source_filename, start_time, duration, description)
clips_metadata = [
    (
        "12647598_1920_1080_50fps.mp4", 
        "00:00:00", 
        "00:00:04", 
        "Drone overview of Afghan city/fields"
    ),
    (
        "Women’s rights being rolled back in Afghanistan - BBC News-(720p50).mp4", 
        "00:04:14", 
        "00:00:04", 
        "Taliban soldiers/patrol on Kabul streets"
    ),
    (
        "FRANCE 24 report： The Afghan girls defying Taliban bans to go to school • FRANCE 24 English-(1080p25).mp4", 
        "00:00:12", 
        "00:00:05", 
        "Girls entering secret school doorway"
    ),
    (
        "FRANCE 24 report： The Afghan girls defying Taliban bans to go to school • FRANCE 24 English-(1080p25).mp4", 
        "00:01:54", 
        "00:00:05", 
        "Close-up of student writing in notebook"
    ),
    (
        "Women’s rights being rolled back in Afghanistan - BBC News-(720p50).mp4", 
        "00:01:55", 
        "00:00:05", 
        "Silhouette of girl looking out the window"
    ),
    (
        "Afghanistan under the Taliban ｜ DW Documentary-(1080p25).mp4", 
        "00:11:56", 
        "00:00:06", 
        "Dignified portrait of masked girl on rooftop overlooking Kabul"
    )
]

print("Cutting and normalizing clips...")
normalized_files = []

for idx, (filename, start, duration, desc) in enumerate(clips_metadata):
    input_path = os.path.join(base_dir, filename)
    temp_cut = os.path.join(temp_dir, f"cut_{idx}.mp4")
    temp_norm = os.path.join(temp_dir, f"norm_{idx}.mp4")
    
    print(f"Processing Clip {idx+1}: {desc}")
    
    # Cut clip
    cut_cmd = [
        "ffmpeg", "-y", "-ss", start, "-i", input_path, "-t", duration,
        "-c", "copy", temp_cut
    ]
    subprocess.run(cut_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Normalize clip: scale/pad to 1920x1080, 25fps, strip audio (-an), yuv420p
    norm_cmd = [
        "ffmpeg", "-y", "-i", temp_cut,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-r", "25", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", temp_norm
    ]
    subprocess.run(norm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    normalized_files.append(temp_norm)

# Write concat list file
concat_list_path = os.path.join(temp_dir, "concat_list.txt")
with open(concat_list_path, "w") as f:
    for file_path in normalized_files:
        f.write(f"file '{file_path}'\n")

# Merge clips
output_path = os.path.join(base_dir, "afghanistan_broll_compilation.mp4")
print("Merging clips into final compilation...")
merge_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-c", "copy", output_path
]
subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Clean up temp files
print("Cleaning up temporary files...")
for file in os.listdir(temp_dir):
    os.remove(os.path.join(temp_dir, file))
os.rmdir(temp_dir)

print(f"Success! Final B-roll compilation created at: {output_path}")
