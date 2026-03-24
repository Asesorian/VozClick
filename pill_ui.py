"""
DictaFlow — Pill UI v2
Variable width, waveform visualizer, drawn status icons.
Base: Daniel's sflow Mac (pill_widget + audio_visualizer combined)
"""
import math
import queue
import logging
import numpy as np
from enum import Enum
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QLinearGradient
from PyQt6.QtWidgets import QWidget, QApplication

from config import (
    PILL_WIDTH_IDLE, PILL_WIDTH_RECORDING, PILL_WIDTH_STATUS,
    PILL_HEIGHT, PILL_CORNER_RADIUS, PILL_MARGIN_BOTTOM,
    NUM_BARS, VIZ_FPS, BAR_DECAY, BAR_GAIN,
)

logger = logging.getLogger(__name__)


class PillState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class PillUI(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self._db = db
        self._state = PillState.IDLE

        # Width animation
        self._target_width = PILL_WIDTH_IDLE
        self._current_width = float(PILL_WIDTH_IDLE)

        # Waveform visualizer
        self._bar_values = [0.0] * NUM_BARS
        self._audio_queue: queue.Queue | None = None

        # Status icons
        self._spinner_angle = 0

        # Drag
        self._drag_pos = None

        self._setup_window()

        # Animation timer (60fps for smooth width + waveform)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(16)

        # Spinner timer
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(50)
        self._spinner_timer.timeout.connect(self._tick_spinner)

        # Auto-return to idle after done/error
        self._done_timer = QTimer(self)
        self._done_timer.setSingleShot(True)
        self._done_timer.timeout.connect(lambda: self.set_state(PillState.IDLE))

        self._position_on_screen()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedHeight(PILL_HEIGHT)
        self.setFixedWidth(PILL_WIDTH_IDLE)

    def _position_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.center().x() - int(self._current_width) // 2
            y = geo.bottom() - PILL_MARGIN_BOTTOM - PILL_HEIGHT
            self.move(x, y)

    def set_audio_queue(self, q: queue.Queue):
        self._audio_queue = q

    def set_state(self, state: PillState):
        self._state = state
        self._spinner_timer.stop()

        if state == PillState.IDLE:
            self._target_width = PILL_WIDTH_IDLE
        elif state == PillState.RECORDING:
            self._target_width = PILL_WIDTH_RECORDING
        elif state == PillState.PROCESSING:
            self._target_width = PILL_WIDTH_STATUS
            self._spinner_timer.start()
        elif state == PillState.DONE:
            self._target_width = PILL_WIDTH_STATUS
            self._done_timer.start(800)
        elif state == PillState.ERROR:
            self._target_width = PILL_WIDTH_STATUS
            self._done_timer.start(1200)

        self.update()

    def _tick(self):
        # Animate width
        diff = self._target_width - self._current_width
        if abs(diff) > 0.5:
            self._current_width += diff * 0.22
            old_center = self.geometry().center()
            self.setFixedWidth(int(self._current_width))
            new_x = old_center.x() - int(self._current_width) // 2
            self.move(new_x, self.y())

        # Update waveform if recording
        if self._state == PillState.RECORDING and self._audio_queue:
            chunks = []
            while True:
                try:
                    chunks.append(self._audio_queue.get_nowait())
                except queue.Empty:
                    break

            if chunks:
                latest = chunks[-1]
                chunk = latest[:, 0] if latest.ndim > 1 else latest.flatten()
                chunk = chunk.astype(np.float32)
                # Normalize if not already float
                if chunk.max() > 1.0:
                    chunk = chunk / 32768.0
                segments = np.array_split(chunk, NUM_BARS)
                for i, seg in enumerate(segments):
                    if len(seg) > 0:
                        rms = float(np.sqrt(np.mean(seg ** 2)))
                        target = min(rms * BAR_GAIN, 1.0)
                        if target > self._bar_values[i]:
                            self._bar_values[i] = target
                        else:
                            self._bar_values[i] = max(target, self._bar_values[i] * BAR_DECAY)
            else:
                for i in range(NUM_BARS):
                    self._bar_values[i] *= BAR_DECAY
                    if self._bar_values[i] < 0.01:
                        self._bar_values[i] = 0.0
        elif self._state != PillState.RECORDING:
            for i in range(NUM_BARS):
                self._bar_values[i] *= 0.85
                if self._bar_values[i] < 0.01:
                    self._bar_values[i] = 0.0

        self.update()

    def _tick_spinner(self):
        self._spinner_angle = (self._spinner_angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(w), float(h), PILL_CORNER_RADIUS, PILL_CORNER_RADIUS)
        painter.fillPath(path, QColor(10, 10, 10, 240))

        # Border
        painter.setPen(QPen(QColor(130, 80, 255, 50), 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, w, h, PILL_CORNER_RADIUS, PILL_CORNER_RADIUS)

        # Mic icon (always visible, left side)
        mic_x = 10
        mic_cy = h // 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(200, 180, 255))
        painter.drawRoundedRect(mic_x, mic_cy - 6, 8, 10, 2, 2)
        painter.drawRect(mic_x + 3, mic_cy + 5, 2, 3)
        painter.drawRect(mic_x, mic_cy + 8, 8, 1)

        if self._state == PillState.RECORDING:
            self._draw_waveform(painter, w, h)
        elif self._state == PillState.PROCESSING:
            self._draw_spinner(painter, w, h)
        elif self._state == PillState.DONE:
            self._draw_checkmark(painter, w, h)
        elif self._state == PillState.ERROR:
            self._draw_error(painter, w, h)

        painter.end()

    def _draw_waveform(self, painter: QPainter, w: int, h: int):
        """Smooth waveform with Bezier curves and gradient."""
        content_start = 24
        content_w = w - content_start - 6
        if content_w <= 0:
            return

        cy = h / 2.0
        vals = [0.0] + self._bar_values + [0.0]
        n_pts = len(vals)
        step = content_w / (n_pts - 1)

        path = QPainterPath()

        # Top curve
        pts_top = []
        for i, val in enumerate(vals):
            window = math.sin((i / (n_pts - 1)) * math.pi)
            amp = val * window * (h / 2.0) * 0.9
            if amp < 0.5:
                amp = 0.5
            pts_top.append((content_start + i * step, cy - amp))

        path.moveTo(pts_top[0][0], pts_top[0][1])
        for i in range(n_pts - 1):
            x1, y1 = pts_top[i]
            x2, y2 = pts_top[i + 1]
            ctrl_x = (x1 + x2) / 2.0
            path.cubicTo(ctrl_x, y1, ctrl_x, y2, x2, y2)

        # Bottom curve (mirrored, backwards)
        pts_bot = []
        for i, val in enumerate(vals):
            window = math.sin((i / (n_pts - 1)) * math.pi)
            amp = val * window * (h / 2.0) * 0.9
            if amp < 0.5:
                amp = 0.5
            pts_bot.append((content_start + i * step, cy + amp))

        for i in range(n_pts - 1, 0, -1):
            x1, y1 = pts_bot[i]
            x2, y2 = pts_bot[i - 1]
            ctrl_x = (x1 + x2) / 2.0
            path.cubicTo(ctrl_x, y1, ctrl_x, y2, x2, y2)

        path.closeSubpath()

        # Gradient fill
        gradient = QLinearGradient(content_start, 0, content_start + content_w, 0)
        gradient.setColorAt(0.0, QColor(130, 80, 255, 0))
        gradient.setColorAt(0.15, QColor(130, 80, 255, 140))
        gradient.setColorAt(0.5, QColor(200, 160, 255, 255))
        gradient.setColorAt(0.85, QColor(130, 80, 255, 140))
        gradient.setColorAt(1.0, QColor(130, 80, 255, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawPath(path)

    def _draw_spinner(self, painter: QPainter, w: int, h: int):
        cx = 24 + (w - 24 - 4) // 2
        cy = h // 2
        for i in range(6):
            angle = math.radians(self._spinner_angle + i * 60)
            dx = 5 * math.cos(angle)
            dy = 5 * math.sin(angle)
            alpha = 220 - i * 35
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(200, 180, 255, max(alpha, 30)))
            painter.drawEllipse(int(cx + dx) - 1, int(cy + dy) - 1, 3, 3)

    def _draw_checkmark(self, painter: QPainter, w: int, h: int):
        cx = 24 + (w - 24 - 4) // 2
        cy = h // 2
        pen = QPen(QColor(100, 220, 100), 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(cx - 4, cy, cx - 1, cy + 3)
        painter.drawLine(cx - 1, cy + 3, cx + 5, cy - 3)

    def _draw_error(self, painter: QPainter, w: int, h: int):
        cx = 24 + (w - 24 - 4) // 2
        cy = h // 2
        pen = QPen(QColor(255, 100, 100), 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(cx - 3, cy - 3, cx + 3, cy + 3)
        painter.drawLine(cx - 3, cy + 3, cx + 3, cy - 3)

    # --- Drag support ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
