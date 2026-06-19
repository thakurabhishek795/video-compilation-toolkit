import librosa
import numpy as np

class BackgroundNoiseDetector:
    def detect(self, audio_path):
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)
        
        flatness = librosa.feature.spectral_flatness(y=y)[0]
        times = librosa.times_like(flatness, sr=sr)
        
        events = []
        noise_threshold = 0.5 
        
        in_noise = False
        noise_start = 0
        for i, f in enumerate(flatness):
            if f > noise_threshold and not in_noise:
                in_noise = True
                noise_start = times[i]
            elif f <= noise_threshold and in_noise:
                in_noise = False
                noise_duration = times[i] - noise_start
                if noise_duration > 1.0: 
                    severity = "high" if noise_duration > 3.0 else "medium"
                    events.append({
                        "time": float(noise_start),
                        "duration": float(noise_duration),
                        "severity": severity,
                        "confidence": 0.8
                    })
                    
        return events, duration
