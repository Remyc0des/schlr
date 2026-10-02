import sounddevice as sd
from scipy.io.wavfile import write
import wavio as wv
import os
import numpy as np
from datetime import datetime
class AudioRecorder:
    def __init__(self, freq=16000, output_dir="recordings", on_chunk=None):
        self.freq = freq
        self.output_dir = output_dir
        self.on_chunk = on_chunk
        self.recording = []
        self.stream = None

    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.recording.append(indata.copy())
        if self.on_chunk:
            self.on_chunk(indata[:, 0].copy())   # 1D mono chunk for the transcriber

    def record(self):
        print("Recording... Press ENTER to stop.")
        with sd.InputStream(samplerate=self.freq, channels=2, callback=self.callback):
            input()
        print("Stopping recording...")
        audio = np.concatenate(self.recording, axis=0)
        return audio

    def make_filename(self, course=None):
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if course is not None:
            safe_name = "".join(c for c in course.name if c.isalnum() or c in (" ", "-", "_"))
            safe_name = safe_name.strip().replace(" ", "_")
            base = f"{safe_name}_lecture_{date}"
        else:
             base = f"lecture_{date}"


    def save(self, audio, course=None):
        print("Recording complete. Saving to file...")
        print("Recording exists:", os.path.exists(filename))
        print("Full path:", os.path.abspath(filename))
        write(filename, self.freq, audio)
        wv.write("recording1.wav", audio, self.freq, sampwidth=2)
