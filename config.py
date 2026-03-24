"""
DictaFlow — Configuración centralizada
Lo mejor de sflow + VozFlow
"""
import os
from pathlib import Path

# App info
APP_NAME = "DictaFlow"
APP_VERSION = "1.0.0"
APP_DIR = Path.home() / ".dictaflow"
APP_DIR.mkdir(exist_ok=True)

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
CHUNK_SIZE = 1024
MIN_DURATION_SECONDS = 0.5

# Groq API
GROQ_MODEL = "whisper-large-v3-turbo"
DEFAULT_LANGUAGE = "es"

# Dashboard
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5678"))

# Hotkey polling
POLL_INTERVAL_MS = 30
DOUBLE_TAP_WINDOW = 0.40

# Pill UI
PILL_WIDTH = 120
PILL_HEIGHT = 26

# Available languages
LANGUAGES = {
    "es": "Español",
    "en": "English",
    "pt": "Português",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "ca": "Català",
    "auto": "Auto-detectar",
}
