import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from typing import Dict, Any

from scene_change_detector import detect_scene_changes
from face_tracker import FaceTracker
from emotion_detector import detect_emotions
from object_detector import ObjectDetector
from text_detector import TextDetector
from motion_analyzer import MotionAnalyzer

def run_vision_pipeline(
    video_path: str,
    enable_modules: Dict[str, bool] = None,
    parallel: bool = True
) -> Dict[str, Any]:
    """
    Master Vision Intelligence Pipeline.
    Runs all 6 modules (optionally in parallel) and merges results
    into a single enriched report for DeepSeek-Coder-V2.
    """
    if enable_modules is None:
        enable_modules = {
            "scene_changes": True,
            "faces": True,
            "emotions": True,
            "objects": True,
            "text": True,
            "motion": True
        }

    print(f"🎬 Starting Vision Intelligence Pipeline on: {video_path}")
    start_time = time.time()
    results = {}

    def run_scene_changes():
        print("  🎞️  Scene change detection...")
        return "scene_changes", [asdict(c) for c in detect_scene_changes(video_path)]

    def run_faces():
        print("  👤  Face tracking...")
        tracker = FaceTracker(sample_rate_fps=2)
        return "faces", [asdict(e) for e in tracker.track(video_path)]

    def run_emotions():
        print("  😊  Emotion detection...")
        return "emotions", [asdict(e) for e in detect_emotions(video_path, sample_every_n_sec=2.0)]

    def run_objects():
        print("  📦  Object detection (YOLO)...")
        detector = ObjectDetector(model_size="yolov8n", sample_every_n_sec=1.0)
        return "objects", [asdict(f) for f in detector.detect(video_path)]

    def run_text():
        print("  🔤  Text/OCR detection...")
        detector = TextDetector(languages=["en"], sample_every_n_sec=2.0)
        return "text", [asdict(f) for f in detector.detect(video_path)]

    def run_motion():
        print("  🎥  Motion analysis...")
        analyzer = MotionAnalyzer(sample_every_n_sec=0.5)
        return "motion", [asdict(f) for f in analyzer.analyze(video_path)]

    # Map module names to runner functions
    runners = {
        "scene_changes": run_scene_changes,
        "faces": run_faces,
        "emotions": run_emotions,
        "objects": run_objects,
        "text": run_text,
        "motion": run_motion
    }

    active_runners = [fn for key, fn in runners.items() if enable_modules.get(key, True)]

    if parallel:
        # Run all modules concurrently
        with ThreadPoolExecutor(max_workers=len(active_runners)) as executor:
            futures = {executor.submit(fn): fn.__name__ for fn in active_runners}
            for future in as_completed(futures):
                key, data = future.result()
                results[key] = data
    else:
        # Run sequentially
        for fn in active_runners:
            key, data = fn()
            results[key] = data

    elapsed = round(time.time() - start_time, 1)

    # Build enriched summary for DeepSeek
    summary = {
        "video_path": video_path,
        "processing_time_sec": elapsed,
        "modules_run": list(results.keys()),
        "stats": {
            "scene_changes": len(results.get("scene_changes", [])),
            "face_events": len(results.get("faces", [])),
            "emotion_samples": len(results.get("emotions", [])),
            "mood_shifts": sum(1 for e in results.get("emotions", []) if e.get("mood_shift")),
            "object_frames": len(results.get("objects", [])),
            "text_frames": len(results.get("text", [])),
            "existing_lower_thirds": sum(1 for t in results.get("text", []) if t.get("has_lower_third")),
            "motion_frames": len(results.get("motion", [])),
            "shaky_frames": sum(1 for m in results.get("motion", []) if m.get("motion_type") == "shake"),
            "stable_frames": sum(1 for m in results.get("motion", []) if m.get("is_stable")),
        }
    }

    report = {
        "summary": summary,
        "vision_data": results
    }

    print(f"\n✅ Vision pipeline complete in {elapsed}s")
    print(f"   Scene changes: {summary['stats']['scene_changes']}")
    print(f"   Face events: {summary['stats']['face_events']}")
    print(f"   Mood shifts: {summary['stats']['mood_shifts']}")
    print(f"   Shaky frames: {summary['stats']['shaky_frames']}")
    print(f"   Existing lower thirds: {summary['stats']['existing_lower_thirds']}")

    return report

# Usage — feed output directly to DeepSeek-Coder-V2
if __name__ == "__main__":
    report = run_vision_pipeline(
        video_path="my_video.mp4",
        enable_modules={
            "scene_changes": True,
            "faces": True,
            "emotions": True,
            "objects": True,
            "text": True,
            "motion": True
        },
        parallel=True  # Set False to debug sequentially
    )

    # Save report
    with open("vision_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n📄 Vision report saved to vision_report.json")
    print("🧠 Ready to send to DeepSeek-Coder-V2 for storyboard generation!")
