"""
DictaFlow — Hotkey Manager (Win32 polling)
Base: sflow (Joel Tabasco) — más fiable que pynput
Modificado: Ctrl+Alt (no genera caracteres visibles)
"""
import time
import logging
import win32api
import win32con
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from config import POLL_INTERVAL_MS, DOUBLE_TAP_WINDOW

logger = logging.getLogger(__name__)

VK_CTRL = win32con.VK_CONTROL
VK_ALT = win32con.VK_MENU
VK_SHIFT = win32con.VK_SHIFT


class HotkeyManager(QObject):
    """
    Two recording modes:
    - Push-to-talk: hold Ctrl+Alt, release to stop
    - Hands-free:   double-tap Shift (alone), single Shift tap to stop
    """
    hotkey_pressed = pyqtSignal()
    hotkey_released = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._held = False
        self._hands_free = False
        self._shift_was_down = False
        self._shift_last_up = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)

    def register(self) -> bool:
        self._timer.start(POLL_INTERVAL_MS)
        logger.info("Hotkeys: Ctrl+Alt (push-to-talk) | double-tap Shift (hands-free)")
        return True

    def unregister(self):
        self._timer.stop()

    def _poll(self):
        ctrl = bool(win32api.GetAsyncKeyState(VK_CTRL) & 0x8000)
        alt = bool(win32api.GetAsyncKeyState(VK_ALT) & 0x8000)
        shift = bool(win32api.GetAsyncKeyState(VK_SHIFT) & 0x8000)
        now = time.monotonic()

        # --- Push-to-talk: Ctrl+Alt ---
        ptt = ctrl and alt and not shift
        if ptt and not self._held and not self._hands_free:
            self._held = True
            logger.info("PTT start")
            self.hotkey_pressed.emit()
        elif not ptt and self._held:
            self._held = False
            logger.info("PTT stop")
            self.hotkey_released.emit()

        # --- Hands-free: double-tap Shift alone ---
        shift_alone = shift and not ctrl and not alt

        if not self._held:
            if not self._hands_free:
                if shift_alone and not self._shift_was_down:
                    self._shift_was_down = True
                elif not shift_alone and self._shift_was_down:
                    self._shift_was_down = False
                    dt = now - self._shift_last_up
                    if 0.05 < dt < DOUBLE_TAP_WINDOW:
                        self._hands_free = True
                        self._shift_last_up = 0.0
                        logger.info("Hands-free start")
                        self.hotkey_pressed.emit()
                    else:
                        self._shift_last_up = now
            else:
                if shift_alone and not self._shift_was_down:
                    self._shift_was_down = True
                elif not shift_alone and self._shift_was_down:
                    self._shift_was_down = False
                    self._hands_free = False
                    logger.info("Hands-free stop")
                    self.hotkey_released.emit()
