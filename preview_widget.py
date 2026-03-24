"""
DictaFlow — Vista previa lado a lado (Original vs Refinado)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class PreviewWidget(QWidget):
    choice_made = pyqtSignal(str)  # Emits chosen text, empty string = keep original

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(700, 480)

        self.original_text = ""
        self.refined_text = ""
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
            QTextEdit {
                background-color: rgba(30,30,30,255);
                color: #E2E8F0;
                border: 1px solid rgba(255,255,255,10);
                border-radius: 8px;
                padding: 12px;
                font-family: 'Consolas', monospace;
                font-size: 13px;
            }
            QTextEdit:focus { border: 1px solid rgba(124,58,237,100); }
            QPushButton { font-family: 'Segoe UI'; font-size: 13px; font-weight: 600; border-radius: 8px; padding: 10px 18px; }
            QPushButton#btn_original { background-color: rgba(255,255,255,10); color: #94A3B8; border: 1px solid rgba(255,255,255,15); }
            QPushButton#btn_original:hover { background-color: rgba(255,255,255,20); color: #FFF; }
            QPushButton#btn_refined { background-color: #7c3aed; color: #FFF; border: none; }
            QPushButton#btn_refined:hover { background-color: #6d28d9; }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Compara y elige")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Two columns
        cols = QHBoxLayout()
        cols.setSpacing(16)

        # Original
        orig_col = QVBoxLayout()
        orig_label = QLabel("Original (ya pegado)")
        orig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.orig_edit = QTextEdit()
        self.orig_edit.setReadOnly(True)
        btn_original = QPushButton("Mantener original")
        btn_original.setObjectName("btn_original")
        btn_original.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_original.clicked.connect(self._keep_original)
        orig_col.addWidget(orig_label)
        orig_col.addWidget(self.orig_edit)
        orig_col.addWidget(btn_original)

        # Refined
        ref_col = QVBoxLayout()
        ref_label = QLabel("✨ Refinado (editable)")
        ref_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ref_edit = QTextEdit()
        btn_refined = QPushButton("✨ Usar refinado (reemplazar)")
        btn_refined.setObjectName("btn_refined")
        btn_refined.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refined.clicked.connect(self._use_refined)
        ref_col.addWidget(ref_label)
        ref_col.addWidget(self.ref_edit)
        ref_col.addWidget(btn_refined)

        cols.addLayout(orig_col)
        cols.addLayout(ref_col)
        layout.addLayout(cols)

        main_layout.addWidget(container)

    def show_preview(self, original: str, refined: str):
        self.original_text = original
        self.refined_text = refined
        self.orig_edit.setPlainText(original)
        self.ref_edit.setPlainText(refined)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)

        self.show()

    def _keep_original(self):
        self.choice_made.emit("")
        self.hide()

    def _use_refined(self):
        self.choice_made.emit(self.ref_edit.toPlainText())
        self.hide()
