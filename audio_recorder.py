"""
DictaFlow — Grabador de audio
Base: sflow (Win32, pre-warm stream) + VozFlow (selector micrófono, arranque sin mic)
"""
import io
import wave
import logging
import threading
import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from config import SAMPLE_RATE, CHANNELS, DTYPE, CHUNK_SIZE, MIN_DURATION_SECONDS

logger = logging.getLogger(__name__)


class AudioRecorder(QObject):
    rms_signal = pyqtSignal(float)

    def __init__(self, device_index: int | None = None, sample_rate: int = SAMPLE_RATE, parent=None):
        super().__init__(parent)
        self.sample_rate = sample_rate
        self._device_index = device_index
        self.is_recording = False
        self._buffer: np.ndarray = np.array([], dtype=np.float32)
        self._lock = threading.Lock()
        self._latest_rms: float = 0.0

        # Try to open audio stream — gracefully handle missing devices
        self._stream = None
        self._init_stream()

        # Poll RMS on main thread every 50ms
        self._rms_timer = QTimer(self)
        self._rms_timer.timeout.connect(self._emit_rms)
        self._rms_timer.start(50)

    def _init_stream(self) -> bool:
        """Try to open audio stream. Returns True if successful."""
        if self._stream is not None:
            return True
        try:
            kwargs = dict(
                samplerate=self.sample_rate,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SIZE,
                callback=self._audio_callback,
            )
            if self._device_index is not None:
                kwargs["device"] = self._device_index

            self._stream = sd.InputStream(**kwargs)
            self._stream.start()
            dev_name = sd.query_devices(self._device_index or sd.default.device[0], kind="input")["name"]
            logger.info(f"Audio stream opened: {dev_name}")
            return True
        except Exception as e:
            logger.warning(f"No audio device available: {e}")
            self._stream = None
            return False

    def set_device(self, device_index: int):
        """Change audio device. Closes current stream and reopens."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self._device_index = device_index
        self._init_stream()

    def start(self):
        if self.is_recording:
            return
        if not self._init_stream():
            logger.warning("Cannot record — no audio device available")
            return
        with self._lock:
            self._buffer = np.array([], dtype=np.float32)
        self.is_recording = True

    def stop(self):
        self.is_recording = False
        with self._lock:
            duration = len(self._buffer) / self.sample_rate
            logger.info(f"Buffer on stop: {len(self._buffer)} samples ({duration:.2f}s)")

    def get_wav_if_long_enough(self) -> tuple[bytes, float] | None:
        """Returns (wav_bytes, duration_seconds) or None if too short."""
        with self._lock:
            duration = len(self._buffer) / self.sample_rate
            if duration < MIN_DURATION_SECONDS:
                return None
            return self._encode_wav(self._buffer.copy()), duration

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status):
        if status:
            logger.warning(f"Audio status: {status}")
        mono = indata[:, 0] if indata.ndim > 1 else indata.flatten()
        self._latest_rms = self._calc_rms(mono)
        if self.is_recording:
            with self._lock:
                self._buffer = np.concatenate([self._buffer, mono])

    def _emit_rms(self):
        if self.is_recording:
            self.rms_signal.emit(self._latest_rms)

    @staticmethod
    def _calc_rms(samples: np.ndarray) -> float:
        if len(samples) == 0:
            return 0.0
        return float(np.sqrt(np.mean(samples ** 2)))

    def _encode_wav(self, samples: np.ndarray) -> bytes:
        pcm_16 = (samples * 32767).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm_16.tobytes())
        return buf.getvalue()

    def close(self):
        self._rms_timer.stop()
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()

    @staticmethod
    def list_devices() -> list[dict]:
        """List available audio input devices."""
        devices = []
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                devices.append({
                    "index": i,
                    "name": dev["name"],
                    "channels": dev["max_input_channels"],
                    "sample_rate": dev["default_samplerate"],
                })
        return devices
