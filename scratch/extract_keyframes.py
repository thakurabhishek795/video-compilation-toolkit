import os
import subprocess

videos = [
    ("12647598_1920_1080_50fps.mp4", 5),
    ("FRANCE 24 report： The Afghan girls defying Taliban bans to go to school • FRANCE 24 English-(1080p25).mp4", 10),
    ("The Taliban’s rules for women in Afghanistan ｜ Start Here-(1080p25).mp4", 15),
    ("Women’s rights being rolled back in Afghanistan - BBC News-(720p50).mp4", 15),
    ("Afghanistan under the Taliban ｜ DW Documentary-(1080p25).mp4", 30)
]

base_dir = "/Users/athakur/Downloads/taliban"
output_base = os.path.join(base_dir, "keyframes")
os.makedirs(output_base, exist_ok=True)

print("Starting keyframe extraction...")
for filename, interval in videos:
    filepath = os.path.join(base_dir, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
    
    # Create a subfolder for this video
    short_name = filename.split(" ｜ ")[0].split("：")[0].split(" - ")[0][:20].strip().replace(" ", "_")
    output_dir = os.path.join(output_base, short_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Run ffmpeg to extract frames
    print(f"Extracting {filename} every {interval} seconds...")
    cmd = [
        "ffmpeg", "-y", "-i", filepath,
        "-vf", f"fps=1/{interval},scale=480:-1",
        "-q:v", "5",
        os.path.join(output_dir, "frame_%03d.jpg")
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # List generated frames
    frames = sorted(os.listdir(output_dir))
    print(f"Generated {len(frames)} frames in {output_dir}")

print("Done extracting keyframes!")
