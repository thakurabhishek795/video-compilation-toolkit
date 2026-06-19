import librosa
import numpy as np

class AudioWaveformAnalyzer:
    def analyze(self, audio_path):
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)
        
        rms = librosa.feature.rms(y=y)[0]
        times = librosa.times_like(rms, sr=sr)
        
        events = []
        
        silence_threshold = 0.01
        is_silent = rms < silence_threshold
        
        clipping_threshold = 0.99
        clipping_frames = np.where(np.abs(y) > clipping_threshold)[0]
        if len(clipping_frames) > 0:
            events.append({"type": "clipping", "time": float(clipping_frames[0])/sr, "confidence": 1.0})
            
        rms_diff = np.diff(rms)
        drop_threshold = -0.1
        drops = np.where(rms_diff < drop_threshold)[0]
        for d in drops:
            events.append({"type": "music_drop", "time": float(times[d]), "confidence": min(float(abs(rms_diff[d]))*5, 1.0)})
            
        in_silence = False
        silence_start = 0
        for i, silent in enumerate(is_silent):
            if silent and not in_silence:
                in_silence = True
                silence_start = times[i]
            elif not silent and in_silence:
                in_silence = False
                silence_duration = times[i] - silence_start
                if silence_duration > 0.5:
                    events.append({"type": "silence", "time": float(silence_start), "duration": float(silence_duration), "confidence": 0.9})
                    
        return events, duration
