import torch
import os
import librosa
from pyannote.audio import Pipeline

class SpeakerDiarizer:
    def __init__(self):
        self.auth_token = os.environ.get("HF_TOKEN", "") # Needs token or will fail
        try:
            self.pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=self.auth_token)
            if self.pipeline:
                if torch.backends.mps.is_available():
                    self.pipeline.to(torch.device("mps"))
                elif torch.cuda.is_available():
                    self.pipeline.to(torch.device("cuda"))
        except Exception as e:
            print(f"Failed to load Pyannote pipeline. Did you set HF_TOKEN? Error: {e}")
            self.pipeline = None
            
    def diarize(self, audio_path):
        duration = librosa.get_duration(path=audio_path)
        segments = []
        if not self.pipeline:
            # Fallback if no token provided or error
            print("WARNING: Diarization unavailable. Returning empty segments.")
            return segments, duration
            
        diarization = self.pipeline(audio_path)
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": float(turn.start),
                "end": float(turn.end),
                "speaker_id": str(speaker)
            })
        return segments, duration
