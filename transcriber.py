"""
DictaFlow — Transcriptor Groq Whisper
Base: sflow + VozFlow (soporte idioma)
"""
import io
import logging
from groq import Groq, AuthenticationError, RateLimitError

from config import GROQ_MODEL, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """User-friendly transcription error."""
    pass


class Transcriber:
    def __init__(self, api_key: str, language: str = DEFAULT_LANGUAGE):
        self._client = Groq(api_key=api_key)
        self.language = language

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str | None:
        """Send WAV bytes to Groq Whisper. Returns text or None."""
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            kwargs = dict(file=audio_file, model=GROQ_MODEL)
            if self.language and self.language != "auto":
                kwargs["language"] = self.language

            response = self._client.audio.transcriptions.create(**kwargs)
            text = response.text.strip()
            return text if text else None
        except AuthenticationError:
            logger.error("Groq API key inválida (401)")
            raise TranscriptionError("API key inválida")
        except RateLimitError:
            logger.error("Groq rate limit (429)")
            raise TranscriptionError("Límite de Groq alcanzado")
        except Exception as e:
            logger.error(f"Groq error: {e}")
            raise TranscriptionError("Sin conexión")
