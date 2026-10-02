import queue
import sys
import threading
import traceback

import numpy as np
import torch
from faster_whisper import WhisperModel


class Transcriber:
    """
    Live speech transcription: Silero VAD finds phrases, Whisper transcribes them.

    Live use:
        t = Transcriber()
        t.start()
        t.feed(chunk)      # call with 1D float32 mono 16kHz audio, any chunk size
        t.stop()           # flushes the last phrase and waits for the worker
        print(t.transcript)

    File use:
        text = Transcriber().transcribe_file("recordings/foo.wav")
    """

    SAMPLING_RATE = 16000
    VAD_BLOCK = 512  # Silero needs exactly 512 samples per call at 16kHz

    def __init__(
        self,
        model_size="base",
        device="cpu",
        compute_type="float32",
        beam_size=3,
        on_text=None,
    ):
        self.beam_size = beam_size
        self.on_text = on_text or self._default_on_text

        print("Loading Whisper model...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

        print("Loading Silero VAD...")
        vad_model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad", model="silero_vad", force_reload=False
        )
        VADIterator = utils[3]
        self.vad = VADIterator(vad_model, sampling_rate=self.SAMPLING_RATE)

        # live state
        self.is_speaking = False
        self.segments = []  # finished text pieces, in order
        self._phrase = []  # audio blocks of the phrase being spoken
        self._pending = np.empty(0, dtype=np.float32)  # leftover samples < one block
        self._queue = queue.Queue()
        self._worker = None

    # ---------- public API ----------

    @property
    def transcript(self):
        return " ".join(self.segments)

    def start(self):
        """Reset state and spin up the background worker."""
        self.segments = []
        self._phrase = []
        self._pending = np.empty(0, dtype=np.float32)
        self.is_speaking = False
        self.vad.reset_states()

        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def feed(self, chunk):
        """Accept any-size 1D float32 chunk; re-slices it into VAD-sized blocks."""
        self._pending = np.concatenate([self._pending, chunk.astype(np.float32)])
        while len(self._pending) >= self.VAD_BLOCK:
            block = self._pending[: self.VAD_BLOCK]
            self._pending = self._pending[self.VAD_BLOCK :]
            self._handle_block(block)

    def stop(self):
        """Flush any phrase still in progress, wait for queued audio, shut down."""
        if self.is_speaking:
            self._finish_phrase()
        if self._worker is not None:
            self._queue.put(None)
            self._worker.join()
            self._worker = None
        return self.transcript

    def transcribe_file(self, path):
        """Transcribe a whole audio file (any rate/channels; faster-whisper resamples)."""
        segments, _info = self.model.transcribe(
            str(path), beam_size=self.beam_size, vad_filter=True
        )
        return " ".join(s.text.strip() for s in segments)

    # ---------- internals ----------

    def _handle_block(self, block):
        speech = self.vad(block)

        if self.is_speaking:
            self._phrase.append(block)

        if speech:
            if "start" in speech:
                self.is_speaking = True
                self._phrase = [block]
            if "end" in speech:
                self._finish_phrase()

    def _finish_phrase(self):
        self.is_speaking = False
        if self._phrase:
            self._queue.put(np.concatenate(self._phrase))
        self._phrase = []

    def _worker_loop(self):
        while True:
            audio = self._queue.get()
            if audio is None:
                self._queue.task_done()
                break
            try:
                self._transcribe_phrase(audio)
            except Exception:
                print("Error inside transcription thread!", file=sys.stderr)
                traceback.print_exc()
            finally:
                self._queue.task_done()

    def _transcribe_phrase(self, audio):
        # list() exhausts faster-whisper's lazy generator
        segments, info = self.model.transcribe(
            audio, beam_size=self.beam_size, vad_filter=False
        )
        for seg in list(segments):
            text = seg.text.strip()
            if text:
                self.segments.append(text)
                self.on_text(text, info.language)

    @staticmethod
    def _default_on_text(text, language):
        print(f"[{language}]: {text}", flush=True)


# Standalone live demo, same behavior as the original script
if __name__ == "__main__":
    import sounddevice as sd

    transcriber = Transcriber()
    transcriber.start()

    def callback(indata, frames, time, status):
        if status:
            print(status, flush=True)
        transcriber.feed(indata[:, 0].copy())

    print("Listening live... Press Ctrl+C to stop.")
    with sd.InputStream(
        samplerate=Transcriber.SAMPLING_RATE,
        channels=1,
        blocksize=Transcriber.VAD_BLOCK,
        dtype="float32",
        callback=callback,
    ):
        try:
            while True:
                sd.sleep(1000)
        except KeyboardInterrupt:
            print("\nStopping...")

    transcriber.stop()