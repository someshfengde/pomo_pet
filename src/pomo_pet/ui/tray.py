"""Menu bar integration using QSystemTrayIcon."""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtCore import Qt, QRect


def _create_tray_icon() -> QPixmap:
    """Create a clean green circle icon for the tray."""
    size = 22
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    # Solid green circle
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(52, 199, 89))
    p.drawEllipse(1, 1, size - 2, size - 2)
    # Inner highlight
    p.setBrush(QColor(80, 220, 110))
    p.drawEllipse(4, 3, size - 10, size - 10)
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
        menu.setStyleSheet("""
            QMenu {
                background: rgba(36, 36, 40, 230);
                color: white;
                border: 1px solid rgba(255, 255, 255, 15);
                border-radius: 8px;
                padding: 4px;
                font-family: 'Helvetica Neue';
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(90, 200, 245, 60);
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 10);
                margin: 4px 8px;
            }
        """)

        self.pause_action = menu.addAction("⏸  Pause")
        self.pause_action.triggered.connect(self._toggle_pause)

        reset_action = menu.addAction("↺  Reset Timer")
        reset_action.triggered.connect(self._on_reset)

        menu.addSeparator()

        quit_action = menu.addAction("✕  Quit")
        quit_action.triggered.connect(self._on_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)

        self._is_paused = False

    def show(self):
        self.tray.show()

    def update_timer(self, text: str, phase: str):
        """Update the tray tooltip with current timer."""
        phase_display = phase.replace("_", " ").title()
        emoji = {"Work": "🔴", "Break": "🟢", "Long Break": "🟣"}.get(phase_display, "⚪")
        self.tray.setToolTip(f"Pomo Pet {emoji} {text} — {phase_display}")

    def _toggle_pause(self):
        self._is_paused = not self._is_paused
        self.pause_action.setText("▶  Resume" if self._is_paused else "⏸  Pause")
        if self.on_pause:
            self.on_pause()

    def _on_reset(self):
        self._is_paused = False
        self.pause_action.setText("⏸  Pause")
        if self.on_reset:
            self.on_reset()

    def _on_quit(self):
        if self.on_quit:
            self.on_quit()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            # Single click on tray icon — toggle pause
            self._toggle_pause()
