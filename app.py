"""
DictaFlow — Lo mejor de sflow + VozFlow
Dictado por voz para Windows con dashboard de historial.

Créditos:
  - sflow: Joel Tabasco (Win32 nativo, dashboard, pill animada)
  - VozFlow: Jorge Torres (settings GUI, selector micrófono)
  - Merge: Claude + Jordi
"""
import sys
import os
import logging

# Ensure we run from the script directory (for .env and assets)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal as Signal, QTimer

from config import APP_NAME, DASHBOARD_PORT, DEFAULT_LANGUAGE


class TranscribeWorker(QThread):
    done = Signal(str, float)
    failed = Signal(str)

    def __init__(self, transcriber):
        super().__init__()
        self._transcriber = transcriber
        self.audio_bytes: bytes = b""
        self.duration: float = 0.0

    def run(self):
        from transcriber import TranscriptionError
        try:
            text = self._transcriber.transcribe(self.audio_bytes)
            if text:
                self.done.emit(text, self.duration)
            else:
                self.failed.emit("Sin texto detectado")
        except TranscriptionError as e:
            self.failed.emit(str(e))


def main():
    from db import Database
    from audio_recorder import AudioRecorder
    from transcriber import Transcriber
    from clipboard_paster import ClipboardPaster
    from hotkey_manager import HotkeyManager
    from pill_ui import PillUI, PillState
    from tray_icon import TrayIcon
    from dashboard.server import create_dashboard
    from settings_dialog import SettingsDialog, FirstRunDialog

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_NAME)

    db = Database()

    # --- Load settings from DB ---
    api_key = db.get_setting("api_key") or os.getenv("GROQ_API_KEY", "")
    language = db.get_setting("language", DEFAULT_LANGUAGE)
    device_index_str = db.get_setting("device_index", "")
    device_index = int(device_index_str) if device_index_str else None

    # --- First run: show settings if no API key ---
    if not api_key:
        dialog = FirstRunDialog(db)
        if dialog.exec() != FirstRunDialog.DialogCode.Accepted:
            sys.exit(0)
        api_key = db.get_setting("api_key", "")
        language = db.get_setting("language", DEFAULT_LANGUAGE)
        device_index_str = db.get_setting("device_index", "")
        device_index = int(device_index_str) if device_index_str else None

    if not api_key:
        logger.error("No API key configured, exiting")
        sys.exit(1)

    # --- Init components ---
    recorder = AudioRecorder(device_index=device_index)
    transcriber = Transcriber(api_key=api_key, language=language)
    paster = ClipboardPaster(qt_app=app)
    pill = PillUI(db=db)
    hotkey_mgr = HotkeyManager()
    worker = TranscribeWorker(transcriber)

    # --- Settings dialog callback ---
    def open_settings():
        dialog = SettingsDialog(db)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            # Reload settings
            new_key = db.get_setting("api_key", api_key)
            new_lang = db.get_setting("language", language)
            new_device_str = db.get_setting("device_index", "")

            if new_key and new_key != api_key:
                transcriber._client = None
                from groq import Groq
                transcriber._client = Groq(api_key=new_key)

            transcriber.language = new_lang

            if new_device_str:
                new_device = int(new_device_str)
                if new_device != device_index:
                    recorder.set_device(new_device)

            tray.notify("Configuración guardada")

    tray = TrayIcon(db=db, dashboard_port=DASHBOARD_PORT, on_settings=open_settings)

    # --- Dashboard ---
    create_dashboard(db, DASHBOARD_PORT)

    # --- Hotkey registration ---
    if not hotkey_mgr.register():
        tray.notify("No se pudo activar el hotkey")

    _target_hwnd: list[int] = [0]

    def on_hotkey_pressed():
        import win32gui
        _target_hwnd[0] = win32gui.GetForegroundWindow()
        recorder.start()
        pill.set_state(PillState.RECORDING)
        logger.info("Recording started")

    def on_hotkey_released():
        recorder.stop()
        result = recorder.get_wav_if_long_enough()
        if result is None:
            pill.set_state(PillState.IDLE)
            logger.info("Recording too short, discarded")
            return
        if worker.isRunning():
            logger.warning("Previous transcription still running, discarding")
            pill.set_state(PillState.IDLE)
            return
        wav, duration = result
        pill.set_state(PillState.PROCESSING)
        worker.audio_bytes = wav
        worker.duration = duration
        worker.start()

    def on_rms(value: float):
        pill.set_rms(value)

    def on_transcription_done(text: str, duration: float):
        paster.paste(text, hwnd=_target_hwnd[0])
        current_lang = db.get_setting("language", DEFAULT_LANGUAGE)
        db.save_transcription(text, duration, current_lang)
        pill.set_state(PillState.IDLE)
        logger.info(f"Transcribed ({duration:.1f}s): {text[:80]}")

    def on_transcription_failed(message: str):
        pill.set_state(PillState.ERROR)
        tray.notify(message)
        QTimer.singleShot(3000, lambda: pill.set_state(PillState.IDLE))
        logger.warning(f"Transcription failed: {message}")

    # --- Connect signals ---
    hotkey_mgr.hotkey_pressed.connect(on_hotkey_pressed)
    hotkey_mgr.hotkey_released.connect(on_hotkey_released)
    recorder.rms_signal.connect(on_rms)
    worker.done.connect(on_transcription_done)
    worker.failed.connect(on_transcription_failed)

    # --- Show UI ---
    pill.show()
    tray.show()

    logger.info(f"{APP_NAME} started — Ctrl+Alt (hold) | Shift×2 (hands-free) | dashboard: http://localhost:{DASHBOARD_PORT}")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
