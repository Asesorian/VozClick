"""
VozClick v2 — Lo mejor de sflow + VozFlow + Refiner IA
"""
import sys
import os
import signal
import logging
import threading

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, Qt

from config import APP_NAME, DASHBOARD_PORT, DEFAULT_LANGUAGE, DEFAULT_REFINER_PROVIDER


class VozClickApp(QObject):
    transcription_done = pyqtSignal(str, float)
    transcription_error = pyqtSignal(str)
    refinement_done = pyqtSignal(str, str)
    refinement_error = pyqtSignal(str)

    def __init__(self, qt_app: QApplication):
        super().__init__()
        self._qt_app = qt_app

        # Fast UI init (pill shows immediately)
        from pill_ui import PillUI, PillState
        from db import Database

        self.db = Database()
        self.pill = PillUI(db=self.db)
        self.PillState = PillState

        # Placeholders for deferred components
        self.recorder = None
        self.transcriber = None
        self.hotkey_mgr = None
        self.paster = None
        self.tray = None
        self.refine_widget = None
        self.config_widget = None
        self.preview_widget = None
        self._target_hwnd = [0]

    def start(self):
        self.pill.show()
        self.pill.set_state(self.PillState.PROCESSING)  # Show loading
        QTimer.singleShot(100, self._deferred_setup)

    @pyqtSlot()
    def _deferred_setup(self):
        from audio_recorder import AudioRecorder
        from transcriber import Transcriber
        from clipboard_paster import ClipboardPaster
        from hotkey_manager import HotkeyManager
        from tray_icon import TrayIcon
        from dashboard.server import create_dashboard
        from settings_dialog import SettingsDialog, FirstRunDialog
        from refine_widget import RefineWidget
        from refine_config_widget import RefineConfigWidget
        from preview_widget import PreviewWidget

        # Load settings
        api_key = self.db.get_setting("api_key") or os.getenv("GROQ_API_KEY", "")
        language = self.db.get_setting("language", DEFAULT_LANGUAGE)
        device_str = self.db.get_setting("device_index", "")
        device_index = int(device_str) if device_str else None

        # First run
        if not api_key:
            dialog = FirstRunDialog(self.db)
            if dialog.exec() != FirstRunDialog.DialogCode.Accepted:
                sys.exit(0)
            api_key = self.db.get_setting("api_key", "")
            language = self.db.get_setting("language", DEFAULT_LANGUAGE)
            device_str = self.db.get_setting("device_index", "")
            device_index = int(device_str) if device_str else None

        if not api_key:
            logger.error("No API key, exiting")
            sys.exit(1)

        # Init components
        self.recorder = AudioRecorder(device_index=device_index)
        self.transcriber = Transcriber(api_key=api_key, language=language)
        self.paster = ClipboardPaster(qt_app=self._qt_app)
        self.hotkey_mgr = HotkeyManager()

        # Connect pill to audio queue
        self.pill.set_audio_queue(self.recorder.audio_queue)

        # Refiner widgets
        self.refine_widget = RefineWidget()
        self.refine_widget.refine_requested.connect(self._on_refine_requested, Qt.ConnectionType.QueuedConnection)
        self.config_widget = RefineConfigWidget()
        self.config_widget.generate_requested.connect(self._on_generate_requested, Qt.ConnectionType.QueuedConnection)
        self.preview_widget = PreviewWidget()
        self.preview_widget.choice_made.connect(self._on_preview_choice, Qt.ConnectionType.QueuedConnection)

        # Settings callback
        def open_settings():
            dialog = SettingsDialog(self.db)
            if dialog.exec() == SettingsDialog.DialogCode.Accepted:
                new_key = self.db.get_setting("api_key", api_key)
                new_lang = self.db.get_setting("language", language)
                new_dev = self.db.get_setting("device_index", "")
                if new_key and new_key != api_key:
                    from groq import Groq
                    self.transcriber._client = Groq(api_key=new_key)
                self.transcriber.language = new_lang
                if new_dev:
                    nd = int(new_dev)
                    if nd != device_index:
                        self.recorder.set_device(nd)
                self.tray.notify("Configuración guardada")

        self.tray = TrayIcon(db=self.db, dashboard_port=DASHBOARD_PORT, on_settings=open_settings)

        # Dashboard
        create_dashboard(self.db, DASHBOARD_PORT)

        # Hotkeys
        self.hotkey_mgr.register()
        self.hotkey_mgr.hotkey_pressed.connect(self._on_hotkey_pressed, Qt.ConnectionType.QueuedConnection)
        self.hotkey_mgr.hotkey_released.connect(self._on_hotkey_released, Qt.ConnectionType.QueuedConnection)

        # Transcription signals
        self.transcription_done.connect(self._on_transcription_done, Qt.ConnectionType.QueuedConnection)
        self.transcription_error.connect(self._on_transcription_error, Qt.ConnectionType.QueuedConnection)
        self.refinement_done.connect(self._on_refinement_done, Qt.ConnectionType.QueuedConnection)
        self.refinement_error.connect(self._on_refinement_error, Qt.ConnectionType.QueuedConnection)

        self.tray.show()
        self.pill.set_state(self.PillState.IDLE)
        logger.info(f"{APP_NAME} v2 started — Ctrl+Alt | Shift×2 | dashboard: localhost:{DASHBOARD_PORT}")

    # --- Recording flow ---
    @pyqtSlot()
    def _on_hotkey_pressed(self):
        import win32gui
        self._target_hwnd[0] = win32gui.GetForegroundWindow()
        self.recorder.start()
        self.pill.set_state(self.PillState.RECORDING)

    @pyqtSlot()
    def _on_hotkey_released(self):
        self.recorder.stop()
        duration = self.recorder.get_duration()

        if duration < 0.3:
            self.pill.set_state(self.PillState.IDLE)
            return

        result = self.recorder.get_wav_if_long_enough()
        if result is None:
            self.pill.set_state(self.PillState.IDLE)
            return

        wav, dur = result
        self.pill.set_state(self.PillState.PROCESSING)

        thread = threading.Thread(target=self._transcribe_worker, args=(wav, dur), daemon=True)
        thread.start()

    def _transcribe_worker(self, wav_bytes: bytes, duration: float):
        from transcriber import TranscriptionError
        try:
            text = self.transcriber.transcribe(wav_bytes)
            if text:
                self.transcription_done.emit(text, duration)
            else:
                self.transcription_error.emit("Sin texto detectado")
        except TranscriptionError as e:
            self.transcription_error.emit(str(e))

    @pyqtSlot(str, float)
    def _on_transcription_done(self, text: str, duration: float):
        self.paster.paste(text, hwnd=self._target_hwnd[0])
        lang = self.db.get_setting("language", DEFAULT_LANGUAGE)
        self.db.save_transcription(text, duration, lang)
        self.pill.set_state(self.PillState.DONE)
        logger.info(f"Transcribed ({duration:.1f}s): {text[:80]}")

        # Show refine button
        if self.refine_widget:
            self.refine_widget.show_for_text(text)

    @pyqtSlot(str)
    def _on_transcription_error(self, error: str):
        self.pill.set_state(self.PillState.ERROR)
        if self.tray:
            self.tray.notify(error)
        logger.warning(f"Transcription failed: {error}")

    # --- Refiner flow ---
    @pyqtSlot(str)
    def _on_refine_requested(self, text: str):
        if self.refine_widget:
            self.refine_widget.hide()
        if self.config_widget:
            self.config_widget.show_for_text(text)

    @pyqtSlot(str, str, str)
    def _on_generate_requested(self, text: str, output_type: str, context: str):
        self.pill.set_state(self.PillState.PROCESSING)
        if self.refine_widget:
            self.refine_widget.hide()

        thread = threading.Thread(
            target=self._refine_worker, args=(text, output_type, context), daemon=True
        )
        thread.start()

    def _refine_worker(self, text: str, output_type: str, context: str):
        from refiner import refine_text, RefinerError
        try:
            provider = self.db.get_setting("refiner_provider", DEFAULT_REFINER_PROVIDER)
            # Get the right API key
            if provider == "groq":
                api_key = self.db.get_setting("api_key") or os.getenv("GROQ_API_KEY", "")
            elif provider == "openai":
                api_key = self.db.get_setting("openai_api_key") or os.getenv("OPENAI_API_KEY", "")
            elif provider == "anthropic":
                api_key = self.db.get_setting("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY", "")
            else:
                api_key = ""

            model = self.db.get_setting("refiner_model", "") or None
            refined = refine_text(text, output_type, context, provider, api_key, model)
            self.refinement_done.emit(text, refined)
        except RefinerError as e:
            self.refinement_error.emit(str(e))
        except Exception as e:
            self.refinement_error.emit(str(e))

    @pyqtSlot(str, str)
    def _on_refinement_done(self, original: str, refined: str):
        self.pill.set_state(self.PillState.DONE)
        if self.preview_widget:
            self.preview_widget.show_preview(original, refined)

    @pyqtSlot(str)
    def _on_preview_choice(self, chosen_text: str):
        if chosen_text:
            # Undo original and paste refined
            import win32gui
            hwnd = self._target_hwnd[0]
            # Select all in target and paste refined
            self.paster.paste(chosen_text, hwnd=hwnd)
            logger.info("Refined text accepted and pasted")
        else:
            logger.info("Original text kept")

    @pyqtSlot(str)
    def _on_refinement_error(self, error: str):
        self.pill.set_state(self.PillState.ERROR)
        if self.tray:
            self.tray.notify(f"Refiner: {error}")
        logger.warning(f"Refinement failed: {error}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    vozclick = VozClickApp(qt_app=app)
    vozclick.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
