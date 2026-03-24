"""
DictaFlow — System Tray
Combina: sflow (dashboard) + VozFlow (settings dialog)
"""
import os
import logging
import webbrowser
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

from config import APP_NAME

logger = logging.getLogger(__name__)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, db, dashboard_port: int, on_settings=None, parent=None):
        icon = self._create_icon()
        super().__init__(icon, parent)
        self._db = db
        self._port = dashboard_port
        self._on_settings = on_settings
        self._setup_menu()
        self.setToolTip(f"{APP_NAME} — Ctrl+Alt (hold) · Shift×2 (hands-free)")

    def _create_icon(self) -> QIcon:
        """Create a simple colored circle icon."""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(130, 80, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, size - 8, size - 8)
        # Mic icon (simple lines)
        painter.setPen(QColor("white"))
        painter.setBrush(QColor("white"))
        painter.drawRoundedRect(size // 2 - 5, size // 2 - 10, 10, 14, 3, 3)
        painter.drawRect(size // 2 - 1, size // 2 + 6, 2, 5)
        painter.drawRect(size // 2 - 5, size // 2 + 11, 10, 2)
        painter.end()
        return QIcon(pixmap)

    def _setup_menu(self):
        menu = QMenu()

        dashboard_action = QAction("📊 Historial (dashboard)", menu)
        dashboard_action.triggered.connect(self._open_dashboard)
        menu.addAction(dashboard_action)

        settings_action = QAction("⚙️ Configuración", menu)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("❌ Salir", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _open_dashboard(self):
        webbrowser.open(f"http://localhost:{self._port}")

    def _open_settings(self):
        if self._on_settings:
            self._on_settings()

    def _quit(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def notify(self, message: str):
        self.showMessage(APP_NAME, message, QSystemTrayIcon.MessageIcon.Warning, 4000)
