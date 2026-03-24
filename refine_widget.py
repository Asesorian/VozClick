"""
DictaFlow — Botón flotante "Refinar" (aparece tras transcribir)
"""
from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPainterPath

from config import PILL_MARGIN_BOTTOM, PILL_HEIGHT, REFINE_AUTO_HIDE_MS


class RefineWidget(QWidget):
    refine_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.ToolTip
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(160, 34)

        self._current_text = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.btn = QPushButton("✨ Refinar texto")
        self.btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 10);
                color: #E2E8F0;
                border: 1px solid rgba(255, 255, 255, 15);
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                font-weight: 600;
                border-radius: 8px;
            }
            QPushButton:hover {
                color: #FFFFFF;
                background-color: #7c3aed;
                border: 1px solid #6d28d9;
            }
        """)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(self._on_click)
        layout.addWidget(self.btn)

        self._auto_hide = QTimer(self)
        self._auto_hide.setSingleShot(True)
        self._auto_hide.setInterval(REFINE_AUTO_HIDE_MS)
        self._auto_hide.timeout.connect(self.hide)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(self.width()), float(self.height()), 17, 17)
        painter.fillPath(path, QColor(15, 15, 15, 230))
        painter.setPen(QColor(255, 255, 255, 30))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 17, 17)
        painter.end()

    def show_for_text(self, text: str):
        self._current_text = text
        self.btn.setText("✨ Refinar texto")
        self.btn.setEnabled(True)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.center().x() - self.width() // 2
            y = geo.bottom() - PILL_MARGIN_BOTTOM - PILL_HEIGHT - 44
            self.move(x, y)

        self.show()
        self._auto_hide.start()

    def _on_click(self):
        self.btn.setText("⏳ Abriendo...")
        self.btn.setEnabled(False)
        self._auto_hide.stop()
        self.refine_requested.emit(self._current_text)
