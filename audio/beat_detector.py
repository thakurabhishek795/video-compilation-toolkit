import librosa

class MusicBeatDetector:
    def detect(self, audio_path):
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)
        
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        
        beats = []
        for i, t in enumerate(beat_times):
            frame = beat_frames[i]
            strength = float(onset_env[frame]) if frame < len(onset_env) else 0.5
            is_downbeat = (i % 4 == 0) or (strength > onset_env.mean() * 2)
            beats.append({
                "time": float(t),
                "strength": strength,
                "is_downbeat": bool(is_downbeat)
            })
            
        tempo_val = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
        return {"tempo_bpm": tempo_val, "beats": beats, "total_beats": len(beats)}, duration
