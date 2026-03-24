"""
DictaFlow — Configurador de refinamiento (tipo salida + contexto)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QComboBox, QLineEdit, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class RefineConfigWidget(QWidget):
    generate_requested = pyqtSignal(str, str, str)  # (text, output_type, context)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(560, 500)

        self.original_text = ""
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: rgba(18, 18, 18, 250);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 14px;
            }
            QLabel { color: #FFFFFF; font-family: 'Segoe UI', Arial; font-size: 13px; }
            QTextEdit, QLineEdit, QComboBox {
                background-color: rgba(30, 30, 30, 255);
                color: #E2E8F0;
                border: 1px solid rgba(255, 255, 255, 10);
                border-radius: 8px;
                padding: 10px;
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
            }
            QTextEdit:focus, QLineEdit:focus {
                border: 1px solid rgba(124, 58, 237, 100);
            }
            QComboBox::drop-down { border-left: 1px solid rgba(255,255,255,10); }
            QComboBox QAbstractItemView {
                background-color: rgba(30,30,30,255); color: #E2E8F0;
                selection-background-color: rgba(255,255,255,20);
            }
            QPushButton { font-family: 'Segoe UI'; font-size: 13px; font-weight: 600; border-radius: 8px; padding: 10px 18px; }
            QPushButton#btn_cancel { background-color: rgba(255,255,255,10); color: #94A3B8; border: 1px solid rgba(255,255,255,15); }
            QPushButton#btn_cancel:hover { background-color: rgba(255,255,255,20); color: #FFF; }
            QPushButton#btn_generate { background-color: #7c3aed; color: #FFF; border: none; }
            QPushButton#btn_generate:hover { background-color: #6d28d9; }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("✨ Configurar Refinamiento")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Output type
        type_label = QLabel("Tipo de salida:")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Prompt (estándar)", "Correo electrónico", "Informe",
            "Mensaje Slack/Chat", "Documentación técnica",
            "Lista de tareas", "Guion de vídeo", "Novela",
            "Otra (especificar...)"
        ])
        self.custom_type = QLineEdit()
        self.custom_type.setPlaceholderText("Ej: Artículo de blog, Tuit, Poema...")
        self.custom_type.setVisible(False)
        self.type_combo.currentTextChanged.connect(
            lambda t: self.custom_type.setVisible(t == "Otra (especificar...)")
        )
        layout.addWidget(type_label)
        layout.addWidget(self.type_combo)
        layout.addWidget(self.custom_type)

        # Context
        ctx_label = QLabel("Contexto (¿para qué lo necesitas?):")
        self.ctx_input = QLineEdit()
        self.ctx_input.setPlaceholderText("Ej: Es un correo formal para el jefe sobre el proyecto...")
        layout.addWidget(ctx_label)
        layout.addWidget(self.ctx_input)

        # Base content
        info_label = QLabel("Contenido base (tu dictado):")
        self.info_edit = QTextEdit()
        self.info_edit.setPlaceholderText("Tu texto dictado aparecerá aquí. Puedes editarlo antes de refinar.")
        layout.addWidget(info_label)
        layout.addWidget(self.info_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.hide)

        btn_generate = QPushButton("✨ Refinar")
        btn_generate.setObjectName("btn_generate")
        btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_generate.clicked.connect(self._on_generate)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_generate)
        layout.addLayout(btn_layout)

        main_layout.addWidget(container)

    def show_for_text(self, text: str):
        self.original_text = text
        self.info_edit.setPlainText(text)
        self.ctx_input.clear()
        self.custom_type.clear()
        self.type_combo.setCurrentIndex(0)
        self.custom_type.setVisible(False)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)

        self.show()

    def _on_generate(self):
        txt = self.info_edit.toPlainText().strip()
        typ = self.type_combo.currentText()
        if typ == "Otra (especificar...)":
            typ = self.custom_type.text().strip() or "Texto general"
        ctx = self.ctx_input.text().strip()
        if txt:
            self.generate_requested.emit(txt, typ, ctx)
            self.hide()
