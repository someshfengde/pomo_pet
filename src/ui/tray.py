"""Menu bar integration using QSystemTrayIcon."""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import QTimer


def _create_tray_icon() -> QPixmap:
    """Create a simple avocado emoji icon for the tray."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    font = QFont("Apple Color Emoji", 20)
    p.setFont(font)
    p.drawText(pixmap.rect(), 0x2014, "🥑")  # fallback: green circle
    # Just draw a green circle as fallback
    p.setPen(QColor(0, 0, 0, 0))
    p.setBrush(QColor(52, 199, 89))
    p.drawEllipse(4, 4, 24, 24)
    p.end()
    return pixmap


class TrayManager:
    """Manages the system tray icon and menu."""

    def __init__(self, on_pause=None, on_reset=None, on_quit=None):
        self.on_pause = on_pause
        self.on_reset = on_reset
        self.on_quit = on_quit

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon(_create_tray_icon()))
        self.tray.setToolTip("Pomo Pet")

        # Build menu
        menu = QMenu()

        self.pause_action = menu.addAction("Pause")
        self.pause_action.triggered.connect(self._toggle_pause)

        reset_action = menu.addAction("Reset Timer")
        reset_action.triggered.connect(self._on_reset)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._on_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)

        self._is_paused = False

    def show(self):
        self.tray.show()

    def update_timer(self, text: str, phase: str):
        """Update the tray tooltip with current timer."""
        self.tray.setToolTip(f"Pomo Pet — {text} ({phase})")

    def _toggle_pause(self):
        self._is_paused = not self._is_paused
        self.pause_action.setText("Resume" if self._is_paused else "Pause")
        if self.on_pause:
            self.on_pause()

    def _on_reset(self):
        self._is_paused = False
        self.pause_action.setText("Pause")
        if self.on_reset:
            self.on_reset()

    def _on_quit(self):
        if self.on_quit:
            self.on_quit()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            # Single click on tray icon
            pass
