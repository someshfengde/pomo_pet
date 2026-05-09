"""Design tokens and window configuration."""

from dataclasses import dataclass

from PySide6.QtGui import QColor


class Theme:
    """Apple-inspired design tokens."""

    WIDTH: int = 220
    HEIGHT: int = 290
    CORNER_RADIUS: int = 24
    PADDING: int = 16

    BG = QColor(24, 24, 26, 140)

    TIMER_TEXT_WORK = QColor(52, 199, 89)
    TIMER_TEXT_BREAK = QColor(90, 200, 245)
    PROGRESS_BG = QColor(255, 255, 255, 15)
    PROGRESS_WORK_START = QColor(52, 199, 89)
    PROGRESS_WORK_END = QColor(30, 150, 60)
    PROGRESS_BREAK_START = QColor(90, 200, 245)
    PROGRESS_BREAK_END = QColor(50, 140, 200)

    TEXT_PRIMARY = QColor(255, 255, 255)
    TEXT_SECONDARY = QColor(140, 140, 148)
    TEXT_DIM = QColor(80, 80, 88)

    DOT_FILLED = QColor(255, 200, 50)
    DOT_EMPTY = QColor(50, 50, 55)

    FONT_TIMER: int = 28
    FONT_LABEL: int = 10
    FONT_MESSAGE: int = 11


@dataclass
class WindowConfig:
    """Window configuration."""
    width: int = Theme.WIDTH
    height: int = Theme.HEIGHT
    fps: int = 30
    title: str = "Pomo Pet"
