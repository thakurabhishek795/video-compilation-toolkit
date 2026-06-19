import whisper
import librosa

class AutoTranscriber:
    def __init__(self, model_size="base"):
        print(f"Loading Whisper model ({model_size})...")
        self.model = whisper.load_model(model_size)
        
    def transcribe(self, audio_path):
        duration = librosa.get_duration(path=audio_path)
        result = self.model.transcribe(audio_path)
        
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": float(seg["start"]),
                "end": float(seg["end"]),
                "text": seg["text"]
            })
            
        return {
            "full_text": result.get("text", ""),
            "language": result.get("language", "unknown"),
            "segments": segments
        }, duration
