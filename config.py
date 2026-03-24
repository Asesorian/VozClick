"""
DictaFlow — Configuración centralizada
Lo mejor de sflow + VozFlow + Refiner IA
"""
import os
from pathlib import Path

# App info
APP_NAME = "DictaFlow"
APP_VERSION = "2.0.0"
APP_DIR = Path.home() / ".dictaflow"
APP_DIR.mkdir(exist_ok=True)

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
CHUNK_SIZE = 1024
MIN_DURATION_SECONDS = 0.5

# Groq API (transcription)
GROQ_MODEL = "whisper-large-v3-turbo"
DEFAULT_LANGUAGE = "es"

# Refiner (AI text refinement)
REFINER_PROVIDERS = {
    "groq": {
        "name": "Groq (Llama 3.3 70B — gratis)",
        "model": "llama-3.3-70b-versatile",
        "needs_key": "groq",
    },
    "openai": {
        "name": "OpenAI (GPT-4o)",
        "model": "gpt-4o",
        "needs_key": "openai",
    },
    "anthropic": {
        "name": "Anthropic (Claude Sonnet 4)",
        "model": "claude-sonnet-4-20250514",
        "needs_key": "anthropic",
    },
}
DEFAULT_REFINER_PROVIDER = "groq"

# Dashboard
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5678"))

# Hotkey polling
POLL_INTERVAL_MS = 30
DOUBLE_TAP_WINDOW = 0.40

# Pill UI — variable width per state
PILL_WIDTH_IDLE = 34
PILL_WIDTH_RECORDING = 130
PILL_WIDTH_STATUS = 52
PILL_HEIGHT = 34
PILL_CORNER_RADIUS = 17
PILL_MARGIN_BOTTOM = 14

# Audio Visualizer
NUM_BARS = 16
VIZ_FPS = 30
BAR_DECAY = 0.80
BAR_GAIN = 6.0

# Refine widget
REFINE_AUTO_HIDE_MS = 8000

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
