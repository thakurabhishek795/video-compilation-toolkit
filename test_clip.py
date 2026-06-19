import core
import os
media_dir = "/Users/athakur/Downloads/taliban"
videos = core.get_videos(media_dir)
test_video = videos[0]
clips = [{"video": test_video, "start": "00:00:00", "duration": "00:00:03", "out_name": "test_clip.mp4"}]
try:
    core.export_individual_clips(media_dir, clips)
except Exception as e:
    print(e)
