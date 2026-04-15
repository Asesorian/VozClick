"""
VozClick — Diálogo de Configuración v2
Incluye: API key, micrófono, idioma, inicio Windows, Refiner IA (multi-provider)
"""
import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QGroupBox,
    QMessageBox, QCheckBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from audio_recorder import AudioRecorder
from config import APP_NAME, LANGUAGES, APP_DIR, REFINER_PROVIDERS, DEFAULT_REFINER_PROVIDER


def get_startup_folder() -> Path:
    return Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup"

def is_startup_enabled() -> bool:
    return (get_startup_folder() / f"{APP_NAME}.lnk").exists()

def enable_startup() -> bool:
    try:
        shortcut_path = get_startup_folder() / f"{APP_NAME}.lnk"
        script_dir = Path(__file__).parent
        target = script_dir / "launch.vbs"
        if not target.exists():
            target = script_dir / "launch.bat"
        ps_command = f'''
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "wscript.exe"
        $Shortcut.Arguments = "{target}"
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
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self._db = db
        self.setWindowTitle(f"{APP_NAME} — Configuración")
        self.setFixedSize(480, 560)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel(APP_NAME)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "General")
        tabs.addTab(self._create_refiner_tab(), "✨ Refiner IA")
        layout.addWidget(tabs)

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

    def _create_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # API Key
        api_group = QGroupBox("API Key de Groq (transcripción)")
        api_layout = QVBoxLayout(api_group)
        api_info = QLabel("Gratis en console.groq.com/keys (~300 min/día)")
        api_info.setStyleSheet("color: gray; font-size: 11px;")
        api_layout.addWidget(api_info)
        self._api_input = QLineEdit()
        self._api_input.setPlaceholderText("gsk_...")
        self._api_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self._db.get_setting("api_key"):
            self._api_input.setText("••••••••••••••••")
        api_layout.addWidget(self._api_input)
        layout.addWidget(api_group)

        # Microphone
        mic_group = QGroupBox("Micrófono")
        mic_layout = QVBoxLayout(mic_group)
        self._mic_combo = QComboBox()
        saved_dev = self._db.get_setting("device_index", "")
        for dev in AudioRecorder.list_devices():
            self._mic_combo.addItem(dev["name"], dev["index"])
            if saved_dev and str(dev["index"]) == saved_dev:
                self._mic_combo.setCurrentIndex(self._mic_combo.count() - 1)
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
        self._startup_check = QCheckBox(f"Iniciar {APP_NAME} con Windows")
        self._startup_check.setChecked(is_startup_enabled())
        startup_layout.addWidget(self._startup_check)
        layout.addWidget(startup_group)

        # Hotkeys info
        info_group = QGroupBox("Atajos de teclado")
        info_layout = QVBoxLayout(info_group)
        info_layout.addWidget(QLabel(
            "• Ctrl + Alt (mantener): Grabar y pegar\n"
            "• Shift × 2 (doble tap): Modo manos libres\n"
            "• Dashboard: localhost:5678"
        ))
        layout.addWidget(info_group)

        layout.addStretch()
        return tab

    def _create_refiner_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        info = QLabel(
            "El Refiner toma tu texto dictado y lo estructura como email,\n"
            "informe, prompt, etc. Aparece un botón ✨ tras cada transcripción."
        )
        info.setStyleSheet("color: gray; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Provider
        prov_group = QGroupBox("Proveedor de IA")
        prov_layout = QVBoxLayout(prov_group)
        self._provider_combo = QComboBox()
        current_prov = self._db.get_setting("refiner_provider", DEFAULT_REFINER_PROVIDER)
        for key, prov in REFINER_PROVIDERS.items():
            self._provider_combo.addItem(prov["name"], key)
            if key == current_prov:
                self._provider_combo.setCurrentIndex(self._provider_combo.count() - 1)
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        prov_layout.addWidget(self._provider_combo)

        prov_note = QLabel("Groq usa la misma API key que la transcripción (gratis).")
        prov_note.setStyleSheet("color: gray; font-size: 11px;")
        prov_layout.addWidget(prov_note)
        layout.addWidget(prov_group)

        # OpenAI key
        self._openai_group = QGroupBox("API Key de OpenAI")
        openai_layout = QVBoxLayout(self._openai_group)
        self._openai_input = QLineEdit()
        self._openai_input.setPlaceholderText("sk-...")
        self._openai_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self._db.get_setting("openai_api_key"):
            self._openai_input.setText("••••••••••••••••")
        openai_layout.addWidget(self._openai_input)
        layout.addWidget(self._openai_group)

        # Anthropic key
        self._anthropic_group = QGroupBox("API Key de Anthropic")
        anthropic_layout = QVBoxLayout(self._anthropic_group)
        self._anthropic_input = QLineEdit()
        self._anthropic_input.setPlaceholderText("sk-ant-...")
        self._anthropic_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self._db.get_setting("anthropic_api_key"):
            self._anthropic_input.setText("••••••••••••••••")
        anthropic_layout.addWidget(self._anthropic_input)
        layout.addWidget(self._anthropic_group)

        # Model override
        model_group = QGroupBox("Modelo (dejar vacío = default)")
        model_layout = QVBoxLayout(model_group)
        self._model_input = QLineEdit()
        self._model_input.setPlaceholderText("Ej: llama-3.3-70b-versatile, gpt-4o, claude-sonnet-4-20250514")
        saved_model = self._db.get_setting("refiner_model", "")
        if saved_model:
            self._model_input.setText(saved_model)
        model_layout.addWidget(self._model_input)
        layout.addWidget(model_group)

        self._on_provider_changed()
        layout.addStretch()
        return tab

    def _on_provider_changed(self):
        prov = self._provider_combo.currentData()
        self._openai_group.setVisible(prov == "openai")
        self._anthropic_group.setVisible(prov == "anthropic")

    def _save(self):
        # Groq API key
        api_key = self._api_input.text().strip()
        if api_key and not api_key.startswith("•"):
            if not api_key.startswith("gsk_"):
                QMessageBox.warning(self, "Error", "La API key de Groq debe empezar con 'gsk_'")
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

        # Refiner provider
        prov = self._provider_combo.currentData()
        if prov:
            self._db.set_setting("refiner_provider", prov)

        # OpenAI key
        oai_key = self._openai_input.text().strip()
        if oai_key and not oai_key.startswith("•"):
            self._db.set_setting("openai_api_key", oai_key)

        # Anthropic key
        ant_key = self._anthropic_input.text().strip()
        if ant_key and not ant_key.startswith("•"):
            self._db.set_setting("anthropic_api_key", ant_key)

        # Model override
        model = self._model_input.text().strip()
        self._db.set_setting("refiner_model", model)

        self.accept()


class FirstRunDialog(SettingsDialog):
    def __init__(self, db, parent=None):
        super().__init__(db, parent)
        self.setWindowTitle(f"Bienvenido a {APP_NAME}")
