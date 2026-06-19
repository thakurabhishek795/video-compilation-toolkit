import core
import os

media_dir = "/Users/athakur/Downloads/taliban"
print("1. Testing get_videos...")
videos = core.get_videos(media_dir)
print(f"Found {len(videos)} videos.")

if len(videos) > 0:
    test_video = videos[0]
    
    # Test 2: Keyframes
    print("\n2. Testing generate_keyframes_and_sheets...")
    try:
        res = core.generate_keyframes_and_sheets(media_dir)
        print("Keyframes generated.")
    except Exception as e:
        print("Keyframes error:", e)

    # Test 3: Suggest Name (moondream)
    print("\n3. Testing suggest_video_name (moondream)...")
    try:
        name = core.suggest_video_name(media_dir, test_video, "moondream")
        print("Suggested name:", name)
    except Exception as e:
        print("Suggest name error:", e)

    # Test 4: Storyboard (moondream hybrid)
    print("\n4. Testing generate_storyboard (moondream hybrid)...")
    script = "This is a test script about women in Afghanistan."
    try:
        board = core.generate_storyboard(media_dir, script, "moondream")
        print("Storyboard generated with", len(board), "scenes.")
    except Exception as e:
        print("Storyboard error:", e)

    # Test 5: Compile Clip
    print("\n5. Testing export_individual_clips...")
    clips = [{"video": test_video, "start": "00:00:00", "duration": "00:00:03", "out_name": "test_clip.mp4"}]
    try:
        core.export_individual_clips(media_dir, clips)
        if os.path.exists(os.path.join(media_dir, "test_clip.mp4")):
            print("Clip exported successfully.")
        else:
            print("Clip export failed.")
    except Exception as e:
        print("Clip export error:", e)

else:
    print("No videos found to test.")
