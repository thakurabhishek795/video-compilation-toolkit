"""
Audio Intelligence Pipeline - Master Orchestrator
Runs 5 audio analysis modules in parallel and merges results into audio_report.json
Part of the Hybrid AI Video Director system (Moondream + DeepSeek-Coder-V2)
"""

import json
import logging
import subprocess
import sys
import tempfile
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Third-party imports
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    VideoFileClip = None

# Audio module imports
from audio.waveform_analyzer import AudioWaveformAnalyzer
from audio.speaker_diarizer import SpeakerDiarizer
from audio.transcriber import AutoTranscriber
from audio.beat_detector import MusicBeatDetector
from audio.noise_detector import BackgroundNoiseDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class StoryboardHint:
    """Storyboard hint from audio insights"""

    timestamp: str  # "0:02:15"
    timestamp_sec: float
    action: str  # insert_broll, music_change, transition, text_overlay, cut_point, audio_fade
    subtype: str
    description: str
    duration_suggestion_sec: float
    confidence: float
    priority: str  # low, medium, high
    audio_source: str
    broll_keywords: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AudioIntelligencePipeline:
    """
    Master orchestrator for audio intelligence analysis.
    Runs 5 audio modules in parallel and generates audio_report.json and audio_storyboard_hints.json
    """

    SUPPORTED_ACTIONS = {
        "insert_broll",
        "music_change",
        "transition",
        "text_overlay",
        "cut_point",
        "audio_fade",
    }

    KEYWORD_PHRASES = {
        "text_overlay": [
            "check this out",
            "look at",
            "here we see",
            "notice",
            "pay attention",
            "see this",
            "watch",
            "observe",
        ]
    }

    def __init__(
        self,
        video_path: Optional[str] = None,
        audio_path: Optional[str] = None,
        whisper_model_size: str = "base",
        output_dir: str = "output/",
        max_workers: int = 5,
    ):
        """
        Initialize Audio Intelligence Pipeline.

        Args:
            video_path: Path to video file (will extract audio)
            audio_path: Path to audio file (WAV/MP3/FLAC)
            whisper_model_size: Whisper model size (tiny, base, small, medium, large)
            output_dir: Directory to save output JSON files
            max_workers: Number of parallel workers for ThreadPoolExecutor
        """
        if not video_path and not audio_path:
            raise ValueError("Either video_path or audio_path must be provided")

        self.video_path = video_path
        self.audio_path = audio_path
        self.whisper_model_size = whisper_model_size
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers

        # Module instances
        self.waveform_analyzer = AudioWaveformAnalyzer()
        self.speaker_diarizer = SpeakerDiarizer()
        self.transcriber = AutoTranscriber(model_size=whisper_model_size)
        self.beat_detector = MusicBeatDetector()
        self.noise_detector = BackgroundNoiseDetector()

        logger.info(f"AudioIntelligencePipeline initialized with max_workers={max_workers}")

    def _extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file.
        Tries moviepy first, falls back to ffmpeg subprocess.

        Args:
            video_path: Path to video file

        Returns:
            Path to extracted audio WAV file

        Raises:
            RuntimeError: If both methods fail
        """
        logger.info(f"Extracting audio from {video_path}")

        # Create temporary file for audio
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        audio_output_path = temp_audio.name
        temp_audio.close()

        # Try moviepy first
        if VideoFileClip is not None:
            try:
                with VideoFileClip(video_path) as video:
                    if video.audio is None:
                        raise ValueError("Video has no audio track")
                    video.audio.write_audiofile(
                        audio_output_path, verbose=False, logger=None
                    )
                logger.info(f"Audio extracted successfully via moviepy: {audio_output_path}")
                return audio_output_path
            except Exception as e:
                logger.warning(f"moviepy extraction failed: {e}. Falling back to ffmpeg.")

        # Fallback to ffmpeg subprocess
        try:
            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-q:a",
                "9",
                "-n",
                audio_output_path,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                if "Output file does not contain any stream" in result.stderr or "Output file does not contain any stream" in result.stdout:
                    raise RuntimeError("No audio track found in this video.")
                raise RuntimeError(f"ffmpeg failed: {result.stderr}")
            logger.info(f"Audio extracted successfully via ffmpeg: {audio_output_path}")
            return audio_output_path
        except RuntimeError as e:
            if "No audio track found" in str(e):
                raise
            raise RuntimeError(f"Failed to extract audio from {video_path}: {e}")
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise RuntimeError(f"Failed to extract audio from {video_path}: {e}")

    def _run_waveform_analysis(self, audio_path: str) -> Dict[str, Any]:
        """Run waveform analyzer module"""
        try:
            logger.info("Starting waveform analysis...")
            events, duration = self.waveform_analyzer.analyze(audio_path)
            logger.info(f"Waveform analysis complete: {len(events)} events detected")
            return {
                "events": events,
                "total_events": len(events),
                "duration_sec": duration,
            }
        except Exception as e:
            logger.error(f"Waveform analysis failed: {e}\n{traceback.format_exc()}")
            return {"events": [], "total_events": 0, "duration_sec": 0.0, "error": str(e)}

    def _run_speaker_diarization(self, audio_path: str) -> Dict[str, Any]:
        """Run speaker diarizer module"""
        try:
            logger.info("Starting speaker diarization...")
            segments, duration = self.speaker_diarizer.diarize(audio_path)
            speaker_ids = sorted(
                list(set([seg.get("speaker_id") for seg in segments]))
            )
            logger.info(
                f"Diarization complete: {len(speaker_ids)} speakers, {len(segments)} segments"
            )
            return {
                "segments": segments,
                "total_speakers": len(speaker_ids),
                "speaker_ids": speaker_ids,
                "duration_sec": duration,
            }
        except Exception as e:
            logger.error(f"Speaker diarization failed: {e}\n{traceback.format_exc()}")
            return {
                "segments": [],
                "total_speakers": 0,
                "speaker_ids": [],
                "duration_sec": 0.0,
                "error": str(e),
            }

    def _run_transcription(self, audio_path: str) -> Dict[str, Any]:
        """Run transcriber module"""
        try:
            logger.info("Starting transcription...")
            transcription, duration = self.transcriber.transcribe(audio_path)
            total_words = len(transcription.get("full_text", "").split())
            logger.info(f"Transcription complete: {total_words} words, {len(transcription.get('segments', []))} segments")
            transcription["total_words"] = total_words
            transcription["duration_sec"] = duration
            return transcription
        except Exception as e:
            logger.error(f"Transcription failed: {e}\n{traceback.format_exc()}")
            return {
                "full_text": "",
                "language": "unknown",
                "segments": [],
                "total_words": 0,
                "duration_sec": 0.0,
                "error": str(e),
            }

    def _run_beat_detection(self, audio_path: str) -> Dict[str, Any]:
        """Run beat detector module"""
        try:
            logger.info("Starting beat detection...")
            beat_report, duration = self.beat_detector.detect(audio_path)
            logger.info(
                f"Beat detection complete: {beat_report.get('tempo_bpm', 0):.1f} BPM, {len(beat_report.get('beats', []))} beats"
            )
            beat_report["duration_sec"] = duration
            return beat_report
        except Exception as e:
            logger.error(f"Beat detection failed: {e}\n{traceback.format_exc()}")
            return {
                "tempo_bpm": 0.0,
                "beats": [],
                "total_beats": 0,
                "duration_sec": 0.0,
                "error": str(e),
            }

    def _run_noise_detection(self, audio_path: str) -> Dict[str, Any]:
        """Run noise detector module"""
        try:
            logger.info("Starting noise detection...")
            events, duration = self.noise_detector.detect(audio_path)
            logger.info(f"Noise detection complete: {len(events)} noise events detected")
            return {
                "events": events,
                "total_flags": len(events),
                "duration_sec": duration,
            }
        except Exception as e:
            logger.error(f"Noise detection failed: {e}\n{traceback.format_exc()}")
            return {"events": [], "total_flags": 0, "duration_sec": 0.0, "error": str(e)}

    def _compute_audio_quality_score(self, audio_report: Dict[str, Any]) -> float:
        """
        Compute audio quality score (0.0-1.0).

        Based on:
        - Noise events count and severity (penalize)
        - Clipping events (heavy penalty)
        - Speech coverage (reward)
        - SNR estimates

        Args:
            audio_report: Audio report dictionary

        Returns:
            Quality score 0.0-1.0
        """
        score = 1.0

        # Penalize noise events
        noise_events = audio_report.get("noise", {}).get("events", [])
        noise_penalty = min(len(noise_events) * 0.02, 0.3)  # Max 30% penalty
        score -= noise_penalty

        # Heavy penalty for clipping
        clipping_events = [
            e for e in audio_report.get("waveform", {}).get("events", [])
            if e.get("type") == "clipping"
        ]
        clipping_penalty = min(len(clipping_events) * 0.1, 0.5)  # Max 50% penalty
        score -= clipping_penalty

        # Reward speech coverage
        duration = audio_report.get("duration_sec", 1.0)
        transcription = audio_report.get("transcription", {})
        speech_segments = transcription.get("segments", [])
        if speech_segments and duration > 0:
            speech_duration = sum(
                seg.get("end", 0) - seg.get("start", 0) for seg in speech_segments
            )
            speech_coverage = speech_duration / duration
            speech_reward = speech_coverage * 0.2  # Max +20% reward
            score += speech_reward

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, score))

    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS or H:MM:SS format"""
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def get_storyboard_hints(self, audio_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert audio insights to storyboard JSON entries.

        Processing:
        - Beats: every downbeat → music_change action
        - Waveform: silence/music drops → cut_point/audio_fade actions
        - Diarization: speaker changes → cut_point action
        - Noise: high-severity noise → insert_broll action
        - Transcription: keyword detection → text_overlay action
        - Deduplication: within 1 second, keep highest confidence
        - Sorting: by timestamp_sec

        Args:
            audio_report: Full audio report dictionary

        Returns:
            List of storyboard hint dictionaries
        """
        hints: List[StoryboardHint] = []
        duration_sec = audio_report.get("duration_sec", 0.0)

        # --- Process beats ---
        beat_report = audio_report.get("beats", {})
        beats = beat_report.get("beats", [])
        tempo_bpm = beat_report.get("tempo_bpm", 0.0)

        for beat in beats:
            beat_time = beat.get("time", 0.0)
            beat_strength = beat.get("strength", 0.5)
            is_downbeat = beat.get("is_downbeat", False)

            if is_downbeat:
                confidence = min(beat_strength, 1.0)
                priority = "high" if confidence > 0.8 else "medium" if confidence > 0.6 else "low"

                hint = StoryboardHint(
                    timestamp=self._seconds_to_timestamp(beat_time),
                    timestamp_sec=beat_time,
                    action="music_change",
                    subtype="downbeat_sync",
                    description=f"Strong downbeat detected — ideal cut point for music sync",
                    duration_suggestion_sec=3.0,
                    confidence=confidence,
                    priority=priority,
                    audio_source="beat_detector",
                    broll_keywords=[],
                )
                hints.append(hint)

        # --- Process waveform events ---
        waveform = audio_report.get("waveform", {})
        waveform_events = waveform.get("events", [])

        for event in waveform_events:
            event_type = event.get("type", "")
            event_time = event.get("time", 0.0)
            confidence = event.get("confidence", 0.7)

            if event_type == "silence":
                hint = StoryboardHint(
                    timestamp=self._seconds_to_timestamp(event_time),
                    timestamp_sec=event_time,
                    action="cut_point",
                    subtype="silence",
                    description="Silence region detected — natural cut point",
                    duration_suggestion_sec=0.5,
                    confidence=confidence,
                    priority="medium",
                    audio_source="waveform_analyzer",
                    broll_keywords=[],
                )
                hints.append(hint)

            elif event_type == "music_drop":
                hint = StoryboardHint(
                    timestamp=self._seconds_to_timestamp(event_time),
                    timestamp_sec=event_time,
                    action="audio_fade",
                    subtype="music_drop",
                    description="Music drop detected — fade out opportunity",
                    duration_suggestion_sec=2.0,
                    confidence=confidence,
                    priority="medium",
                    audio_source="waveform_analyzer",
                    broll_keywords=[],
                )
                hints.append(hint)

        # --- Process diarization speaker changes ---
        diarization = audio_report.get("diarization", {})
        diarization_segments = diarization.get("segments", [])

        for i, segment in enumerate(diarization_segments):
            if i == 0:
                continue  # Skip first segment
            prev_speaker = diarization_segments[i - 1].get("speaker_id", "")
            curr_speaker = segment.get("speaker_id", "")

            if prev_speaker != curr_speaker:
                seg_start = segment.get("start", 0.0)
                hint = StoryboardHint(
                    timestamp=self._seconds_to_timestamp(seg_start),
                    timestamp_sec=seg_start,
                    action="cut_point",
                    subtype="speaker_change",
                    description=f"Speaker change from {prev_speaker} to {curr_speaker}",
                    duration_suggestion_sec=0.3,
                    confidence=0.85,
                    priority="medium",
                    audio_source="speaker_diarizer",
                    broll_keywords=[],
                )
                hints.append(hint)

        # --- Process noise events ---
        noise = audio_report.get("noise", {})
        noise_events = noise.get("events", [])

        for event in noise_events:
            event_time = event.get("time", 0.0)
            severity = event.get("severity", "low")  # low, medium, high
            confidence = event.get("confidence", 0.6)

            if severity in ["high", "critical"]:
                hint = StoryboardHint(
                    timestamp=self._seconds_to_timestamp(event_time),
                    timestamp_sec=event_time,
                    action="insert_broll",
                    subtype="replace_noise",
                    description=f"{severity.capitalize()} noise detected — replace with B-roll",
                    duration_suggestion_sec=2.0,
                    confidence=confidence,
                    priority="high" if severity == "critical" else "medium",
                    audio_source="noise_detector",
                    broll_keywords=["generic", "nature", "office", "music"],
                )
                hints.append(hint)

        # --- Process transcription keyword phrases ---
        transcription = audio_report.get("transcription", {})
        transcript_text = transcription.get("full_text", "").lower()
        transcript_segments = transcription.get("segments", [])

        for phrase in self.KEYWORD_PHRASES.get("text_overlay", []):
            if phrase in transcript_text:
                # Find all occurrences in segments
                for seg in transcript_segments:
                    seg_text = seg.get("text", "").lower()
                    if phrase in seg_text:
                        seg_start = seg.get("start", 0.0)
                        hint = StoryboardHint(
                            timestamp=self._seconds_to_timestamp(seg_start),
                            timestamp_sec=seg_start,
                            action="text_overlay",
                            subtype="keyword_phrase",
                            description=f"Keyword phrase detected: '{phrase}'",
                            duration_suggestion_sec=1.5,
                            confidence=0.8,
                            priority="medium",
                            audio_source="transcriber",
                            broll_keywords=[phrase.replace(" ", "_")],
                        )
                        hints.append(hint)

        # --- Deduplication: keep highest confidence within 1 second ---
        deduplicated = self._deduplicate_hints(hints, threshold_sec=1.0)

        # --- Sort by timestamp_sec ---
        deduplicated.sort(key=lambda h: h.timestamp_sec)

        return [h.to_dict() for h in deduplicated]

    def _deduplicate_hints(
        self, hints: List[StoryboardHint], threshold_sec: float = 1.0
    ) -> List[StoryboardHint]:
        """
        Deduplicate hints within threshold_sec of each other.
        Keeps the highest confidence hint in each cluster.

        Args:
            hints: List of StoryboardHint objects
            threshold_sec: Time threshold for deduplication

        Returns:
            Deduplicated list of hints
        """
        if not hints:
            return []

        # Sort by timestamp
        sorted_hints = sorted(hints, key=lambda h: h.timestamp_sec)

        deduplicated: List[StoryboardHint] = []
        current_cluster: List[StoryboardHint] = []

        for hint in sorted_hints:
            if not current_cluster:
                current_cluster.append(hint)
            elif hint.timestamp_sec - current_cluster[0].timestamp_sec <= threshold_sec:
                current_cluster.append(hint)
            else:
                # End of cluster: keep highest confidence
                best = max(current_cluster, key=lambda h: h.confidence)
                deduplicated.append(best)
                current_cluster = [hint]

        # Handle last cluster
        if current_cluster:
            best = max(current_cluster, key=lambda h: h.confidence)
            deduplicated.append(best)

        return deduplicated

    def run(self, progress_callback=None) -> Dict[str, Any]:
        """
        Run all 5 audio modules in parallel.

        Workflow:
        1. Extract audio if video_path provided
        2. Run all modules concurrently with ThreadPoolExecutor
        3. Gracefully handle individual module failures
        4. Merge results into audio_report.json
        5. Generate storyboard hints
        6. Save audio_storyboard_hints.json
        7. Return full report

        Returns:
            Full audio report dictionary

        Raises:
            RuntimeError: If all modules fail or audio extraction fails
        """
        logger.info("=" * 80)
        logger.info("Audio Intelligence Pipeline - Starting")
        logger.info("=" * 80)

        # Step 1: Extract audio if needed
        if self.video_path:
            self.audio_path = self._extract_audio(self.video_path)
        else:
            logger.info(f"Using provided audio file: {self.audio_path}")

        # Step 2: Run all modules in parallel
        logger.info("Launching all 5 audio modules in parallel...")

        results = {
            "waveform": None,
            "diarization": None,
            "transcription": None,
            "beats": None,
            "noise": None,
        }

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_module = {
                executor.submit(self._run_waveform_analysis, self.audio_path): "waveform",
                executor.submit(self._run_speaker_diarization, self.audio_path): "diarization",
                executor.submit(self._run_transcription, self.audio_path): "transcription",
                executor.submit(self._run_beat_detection, self.audio_path): "beats",
                executor.submit(self._run_noise_detection, self.audio_path): "noise",
            }

            completed_count = 0
            for future in as_completed(future_to_module):
                module_name = future_to_module[future]
                try:
                    result = future.result()
                    results[module_name] = result
                    logger.info(f"✓ {module_name} module completed")
                except Exception as e:
                    logger.error(
                        f"✗ {module_name} module failed: {e}\n{traceback.format_exc()}"
                    )
                    results[module_name] = {"error": str(e)}
                
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count / 5.0, f"Completed {module_name.capitalize()} Analysis...")

        # Step 3: Merge results into audio_report
        duration_sec = max(
            results["waveform"].get("duration_sec", 0) if results["waveform"] else 0,
            results["diarization"].get("duration_sec", 0)
            if results["diarization"]
            else 0,
            results["transcription"].get("duration_sec", 0)
            if results["transcription"]
            else 0,
            results["beats"].get("duration_sec", 0) if results["beats"] else 0,
            results["noise"].get("duration_sec", 0) if results["noise"] else 0,
        )

        audio_report = {
            "video_path": self.video_path,
            "audio_path": str(self.audio_path),
            "duration_sec": duration_sec,
            "sample_rate": 44100,  # Standard CD quality; override if modules provide different
            "waveform": results["waveform"] or {},
            "diarization": results["diarization"] or {},
            "transcription": results["transcription"] or {},
            "beats": results["beats"] or {},
            "noise": results["noise"] or {},
            "summary": {
                "total_speakers": results["diarization"].get("total_speakers", 0)
                if results["diarization"]
                else 0,
                "total_words": results["transcription"].get("total_words", 0)
                if results["transcription"]
                else 0,
                "speech_coverage_pct": 0.0,  # Computed below
                "music_present": len(
                    [e for e in results["beats"].get("beats", []) if e.get("is_downbeat")]
                )
                > 0
                if results["beats"]
                else False,
                "tempo_bpm": results["beats"].get("tempo_bpm", 0.0)
                if results["beats"]
                else 0.0,
                "silence_regions": len(
                    [
                        e
                        for e in results["waveform"].get("events", [])
                        if e.get("type") == "silence"
                    ]
                )
                if results["waveform"]
                else 0,
                "noise_flags": results["noise"].get("total_flags", 0)
                if results["noise"]
                else 0,
                "audio_quality_score": 0.0,  # Computed below
            },
        }

        # Compute speech coverage
        if results["transcription"] and duration_sec > 0:
            speech_segments = results["transcription"].get("segments", [])
            speech_duration = sum(
                seg.get("end", 0) - seg.get("start", 0) for seg in speech_segments
            )
            audio_report["summary"]["speech_coverage_pct"] = (
                speech_duration / duration_sec * 100
            )

        # Compute audio quality score
        audio_report["summary"]["audio_quality_score"] = self._compute_audio_quality_score(
            audio_report
        )

        logger.info(f"Audio report merged: {audio_report['summary']}")

        # Step 4: Generate storyboard hints
        logger.info("Generating storyboard hints...")
        storyboard_hints = self.get_storyboard_hints(audio_report)
        logger.info(f"Generated {len(storyboard_hints)} storyboard hints")

        # Step 5: Save reports
        audio_report_path = self.output_dir / "audio_report.json"
        with open(audio_report_path, "w") as f:
            json.dump(audio_report, f, indent=2)
        logger.info(f"✓ Saved audio_report.json to {audio_report_path}")

        storyboard_hints_path = self.output_dir / "audio_storyboard_hints.json"
        with open(storyboard_hints_path, "w") as f:
            json.dump(storyboard_hints, f, indent=2)
        logger.info(f"✓ Saved audio_storyboard_hints.json to {storyboard_hints_path}")

        logger.info("=" * 80)
        logger.info("Audio Intelligence Pipeline - Complete")
        logger.info("=" * 80)

        return audio_report


def main():
    """CLI entry point for Audio Intelligence Pipeline"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Audio Intelligence Pipeline - Hybrid AI Video Director"
    )
    parser.add_argument(
        "input_file",
        help="Path to video or audio file",
    )
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)",
    )
    parser.add_argument(
        "--output",
        default="output/",
        help="Output directory for JSON reports (default: output/)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of parallel workers (default: 5)",
    )

    args = parser.parse_args()

    # Determine if input is video or audio
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)

    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"}
    audio_extensions = {".wav", ".mp3", ".flac", ".aac", ".ogg", ".m4a"}

    input_ext = input_path.suffix.lower()

    try:
        if input_ext in video_extensions:
            pipeline = AudioIntelligencePipeline(
                video_path=str(input_path),
                whisper_model_size=args.model,
                output_dir=args.output,
                max_workers=args.workers,
            )
        elif input_ext in audio_extensions:
            pipeline = AudioIntelligencePipeline(
                audio_path=str(input_path),
                whisper_model_size=args.model,
                output_dir=args.output,
                max_workers=args.workers,
            )
        else:
            logger.error(f"Unsupported file format: {input_ext}")
            logger.info(f"Supported video: {video_extensions}")
            logger.info(f"Supported audio: {audio_extensions}")
            sys.exit(1)

        report = pipeline.run()

        logger.info("Pipeline completed successfully!")
        logger.info(f"Audio Quality Score: {report['summary']['audio_quality_score']:.2f}")
        logger.info(f"Total Speakers: {report['summary']['total_speakers']}")
        logger.info(f"Total Words: {report['summary']['total_words']}")
        logger.info(f"Speech Coverage: {report['summary']['speech_coverage_pct']:.1f}%")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
