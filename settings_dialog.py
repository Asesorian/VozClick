"""
DictaFlow — Diálogo de Configuración
Base: VozFlow (Jorge Torres) — selector micrófono, idioma, API key, inicio con Windows
"""
import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QGroupBox,
    QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from audio_recorder import AudioRecorder
from config import APP_NAME, LANGUAGES, APP_DIR


def get_startup_folder() -> Path:
    return Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup"


def is_startup_enabled() -> bool:
    return (get_startup_folder() / f"{APP_NAME}.lnk").exists()


def enable_startup() -> bool:
    try:
        shortcut_path = get_startup_folder() / f"{APP_NAME}.lnk"
        script_dir = Path(__file__).parent
        target = script_dir / "launch.bat"
        if not target.exists():
            target = script_dir / "app.py"
        ps_command = f'''
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{target}"
        $Shortcut.WorkingDirectory = "{script_dir}"
        $Shortcut.Description = "{APP_NAME} - Voice to Text"
        $Shortcut.Save()
        '''
        os.system(f'powershell -Command "{ps_command}"')
        return True
    except Exception:
        return False


def disable_startup() -> bool:
    try:
        shortcut = get_startup_folder() / f"{APP_NAME}.lnk"
        if shortcut.exists():
            shortcut.unlink()
        return True
    except Exception:
        return False


class SettingsDialog(QDialog):
    """Settings dialog: API key, microphone, language, startup."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self._db = db
        self.setWindowTitle(f"{APP_NAME} — Configuración")
        self.setFixedSize(420, 480)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel(APP_NAME)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Dictado por voz — lo mejor de sflow + VozFlow")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        # API Key
        api_group = QGroupBox("API Key de Groq")
        api_layout = QVBoxLayout(api_group)
        api_info = QLabel("Gratis en console.groq.com/keys (~300 min/día)")
        api_info.setWordWrap(True)
        api_info.setStyleSheet("color: gray; font-size: 11px;")
        api_layout.addWidget(api_info)

        self._api_input = QLineEdit()
        self._api_input.setPlaceholderText("gsk_...")
        self._api_input.setEchoMode(QLineEdit.EchoMode.Password)

        current_key = self._db.get_setting("api_key")
        if current_key:
            self._api_input.setText("••••••••••••••••")

        api_layout.addWidget(self._api_input)
        layout.addWidget(api_group)

        # Microphone
        mic_group = QGroupBox("Micrófono")
        mic_layout = QVBoxLayout(mic_group)
        self._mic_combo = QComboBox()
        self._load_microphones()
        mic_layout.addWidget(self._mic_combo)
        layout.addWidget(mic_group)

        # Language
        lang_group = QGroupBox("Idioma de transcripción")
        lang_layout = QVBoxLayout(lang_group)
        self._lang_combo = QComboBox()
        current_lang = self._db.get_setting("language", "es")
        for code, name in LANGUAGES.items():
            self._lang_combo.addItem(name, code)
            if code == current_lang:
                self._lang_combo.setCurrentIndex(self._lang_combo.count() - 1)
        lang_layout.addWidget(self._lang_combo)
        layout.addWidget(lang_group)

        # Startup
        startup_group = QGroupBox("Inicio automático")
        startup_layout = QVBoxLayout(startup_group)
        self._startup_check = QCheckBox("Iniciar DictaFlow con Windows")
        self._startup_check.setChecked(is_startup_enabled())
        startup_layout.addWidget(self._startup_check)
        layout.addWidget(startup_group)

        # Hotkeys info
        info_group = QGroupBox("Atajos de teclado")
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel(
            "• Ctrl + Alt (mantener): Grabar y pegar\n"
            "• Shift × 2 (doble tap): Modo manos libres\n"
            "• En manos libres, Shift para detener"
        )
        info_layout.addWidget(info_label)
        layout.addWidget(info_group)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        save_btn = QPushButton("Guardar")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _load_microphones(self):
        saved_device = self._db.get_setting("device_index", "")
        devices = AudioRecorder.list_devices()
        for dev in devices:
            self._mic_combo.addItem(dev["name"], dev["index"])
            if saved_device and str(dev["index"]) == saved_device:
                self._mic_combo.setCurrentIndex(self._mic_combo.count() - 1)

    def _save(self):
        # API key
        api_key = self._api_input.text().strip()
        if api_key and not api_key.startswith("•"):
            if not api_key.startswith("gsk_"):
                QMessageBox.warning(self, "Error", "La API key debe empezar con 'gsk_'")
                return
            self._db.set_setting("api_key", api_key)

        # Microphone
        mic_index = self._mic_combo.currentData()
        if mic_index is not None:
            self._db.set_setting("device_index", str(mic_index))

        # Language
        lang = self._lang_combo.currentData()
        if lang:
            self._db.set_setting("language", lang)

        # Startup
        if self._startup_check.isChecked():
            enable_startup()
        else:
            disable_startup()

        self.accept()


class FirstRunDialog(SettingsDialog):
    """First-run variant — requires API key."""

    def __init__(self, db, parent=None):
        super().__init__(db, parent)
        self.setWindowTitle(f"Bienvenido a {APP_NAME}")
