"""Pet display window using PySide6 (Qt) — clean minimal design."""

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, List, Dict

from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, QRect, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPixmap, QFont, QPen, QBrush, QLinearGradient,
)

from src.pet_loader import AnimationDef


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

class Theme:
    WIDTH: int = 220
    HEIGHT: int = 290
    CORNER_RADIUS: int = 24
    PADDING: int = 16

    # Background
    BG = QColor(24, 24, 26, 200)

    # Timer
    TIMER_TEXT_WORK = QColor(52, 199, 89)
    TIMER_TEXT_BREAK = QColor(90, 200, 245)
    PROGRESS_BG = QColor(255, 255, 255, 15)
    PROGRESS_WORK_START = QColor(52, 199, 89)
    PROGRESS_WORK_END = QColor(30, 150, 60)
    PROGRESS_BREAK_START = QColor(90, 200, 245)
    PROGRESS_BREAK_END = QColor(50, 140, 200)

    # Text
    TEXT_PRIMARY = QColor(255, 255, 255)
    TEXT_SECONDARY = QColor(140, 140, 148)
    TEXT_DIM = QColor(80, 80, 88)

    # Session dots
    DOT_FILLED = QColor(255, 200, 50)
    DOT_EMPTY = QColor(50, 50, 55)

    FONT_TIMER: int = 28
    FONT_LABEL: int = 10
    FONT_MESSAGE: int = 11


@dataclass
class WindowConfig:
    width: int = Theme.WIDTH
    height: int = Theme.HEIGHT
    fps: int = 30
    title: str = "Pomo Pet"


# ---------------------------------------------------------------------------
# PetWindow
# ---------------------------------------------------------------------------

class PetWindow(QMainWindow):

    def __init__(self, pet: Any, config: Optional[WindowConfig] = None, parent=None) -> None:
        super().__init__(parent)
        self.pet = pet
        self.config = config or WindowConfig()

        # State
        self.timer_text: str = "25:00"
        self.timer_phase: str = "WORK"
        self.timer_progress: float = 0.0
        self.message: str = "Let's focus!"
        self.sessions: int = 0
        self.paused: bool = False

        # Animation
        self._animations: Dict[str, List[QPixmap]] = {}
        self._anim_defs: Dict[str, AnimationDef] = {}
        self._current_anim: str = "idle"
        self._frame_index: int = 0
        self._frame_timer: float = 0.0
        self._message_slide: float = 0.0
        self._idle_timer: float = 0.0       # time spent idle
        self._review_toggle: int = 0        # counter for alternating running/review
        self._review_toggle_timer: float = 0.0  # timer for review alternation
        self._pending_anim: Optional[str] = None  # anim to return to after one-shot

        # Drag
        self._drag_pos: Optional[QPoint] = None
        self._drag_prev_x: int = 0
        self._drag_start_pos: Optional[QPoint] = None

        # Callbacks
        self._timer_getter = None
        self._on_toggle_pause = None
        self._on_reset = None
        self._last_phase: Optional[str] = None

        self._setup_window()
        self._load_animations()
        self._setup_timer()

    def _setup_window(self) -> None:
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.config.width, self.config.height)
        self.move(100, 100)

    def _setup_timer(self) -> None:
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(1000 // self.config.fps)

    # ------------------------------------------------------------------
    # Animations
    # ------------------------------------------------------------------

    def _load_animations(self) -> None:
        path = Path(self.pet.spritesheet_path)
        if not path.exists():
            return
        sheet = QPixmap(str(path))
        if sheet.isNull():
            return

        fw = self.pet.frame_width
        fh = self.pet.frame_height
        pet_area = self.config.width - Theme.PADDING * 2
        self._anim_defs = dict(self.pet.animations) if self.pet.animations else {}

        if not self._anim_defs:
            cols = max(sheet.width() // fw, 1)
            rows = max(sheet.height() // fh, 1)
            frames = []
            for r in range(rows):
                for c in range(cols):
                    f = sheet.copy(c * fw, r * fh, fw, fh)
                    frames.append(f.scaled(pet_area, pet_area, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self._animations["idle"] = frames
            self._anim_defs["idle"] = AnimationDef(row=0, frames=len(frames), fps=8, loop=True)
            return

        for name, ad in self._anim_defs.items():
            frames = []
            for col in range(ad.frames):
                f = sheet.copy(col * fw, ad.row * fh, fw, fh)
                frames.append(f.scaled(pet_area, pet_area, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self._animations[name] = frames

    def _set_animation(self, name: str) -> None:
        if name == self._current_anim or name not in self._animations:
            return
        self._current_anim = name
        self._frame_index = 0
        self._frame_timer = 0.0

    def _play_once(self, name: str) -> None:
        """Play a one-shot animation, then return to phase animation."""
        if name not in self._animations:
            return
        self._pending_anim = self._pick_animation(self.timer_phase)
        self._current_anim = name
        self._frame_index = 0
        self._frame_timer = 0.0

    def _pick_animation(self, phase: str) -> str:
        phase = phase.upper()
        if phase == "WORK":
            # Alternate between running and review every ~10 seconds
            if "review" in self._animations and self._review_toggle % 2 == 1:
                return "review"
            for n in ("running", "review", "run_right", "idle"):
                if n in self._animations:
                    return n
        else:
            for n in ("idle", "waiting", "waving"):
                if n in self._animations:
                    return n
        return next(iter(self._animations), "idle")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_timer_text(self, text: str, phase: str) -> None:
        self.timer_text = text
        self.timer_phase = phase

    def set_timer_progress(self, progress: float) -> None:
        self.timer_progress = max(0.0, min(1.0, progress))

    def set_message(self, message: str) -> None:
        if message != self.message:
            self._message_slide = 0.0
        self.message = message

    def set_sessions(self, count: int) -> None:
        self.sessions = count

    def run(self, timer_getter=None, on_toggle_pause=None, on_reset=None) -> None:
        self._timer_getter = timer_getter
        self._on_toggle_pause = on_toggle_pause
        self._on_reset = on_reset
        self.show()

    def quit_window(self) -> None:
        QApplication.instance().quit()

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        dt = 1.0 / self.config.fps

        if self._timer_getter is not None:
            remaining, phase, sessions, message, progress, paused = self._timer_getter()

            # Detect session complete (sessions count increased)
            if sessions > self.sessions and self.sessions > 0:
                self._play_once("waving")

            # Detect phase transition
            if phase != self.timer_phase and self._last_phase is not None:
                # Jumping on phase change (but not if we just played waving)
                if not self._pending_anim:
                    self._play_once("jumping")

            # Detect timer expire (remaining == "00:00")
            if remaining == "00:00" and not paused and not self._pending_anim:
                self._play_once("failed")

            self.set_timer_text(remaining, phase)
            self.set_sessions(sessions)
            self.set_timer_progress(progress)
            self.paused = paused
            if message:
                self.set_message(message)

        # Track phase changes
        if self.timer_phase != self._last_phase:
            self._last_phase = self.timer_phase
            self._review_toggle = 0
            # If no pending one-shot, switch to phase animation
            if not self._pending_anim:
                self._set_animation(self._pick_animation(self.timer_phase))

        # Track idle time for waiting animation
        if self._current_anim == "idle" and not self._pending_anim:
            self._idle_timer += dt
            # After 30 seconds of idle, switch to waiting
            if self._idle_timer >= 30.0 and "waiting" in self._animations:
                self._set_animation("waiting")
                self._idle_timer = 0.0
        else:
            self._idle_timer = 0.0

        # Track work phase time for running/review alternation
        if self._current_anim in ("running", "review") and not self._pending_anim:
            self._review_toggle_timer += dt
            if self._review_toggle_timer >= 10.0:
                self._review_toggle += 1
                self._review_toggle_timer = 0.0
                self._set_animation(self._pick_animation(self.timer_phase))

        self._animate(dt)
        self.update()

    def _animate(self, dt: float) -> None:
        frames = self._animations.get(self._current_anim, [])
        if frames:
            ad = self._anim_defs.get(self._current_anim)
            fps = ad.fps if ad else 8
            self._frame_timer += dt
            if self._frame_timer >= 1.0 / fps:
                self._frame_timer = 0.0
                self._frame_index += 1
                if self._frame_index >= len(frames):
                    if self._pending_anim:
                        # One-shot finished, return to pending
                        next_anim = self._pending_anim
                        self._pending_anim = None
                        self._set_animation(next_anim)
                    elif ad and ad.loop:
                        self._frame_index = 0
                    else:
                        self._frame_index = len(frames) - 1
                        self._set_animation(self._pick_animation(self.timer_phase))

        if self._message_slide < 1.0:
            self._message_slide = min(1.0, self._message_slide + dt * 3.0)

    # ------------------------------------------------------------------
    # Mouse — drag, click (pause), double-click (reset)
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            self._drag_prev_x = event.globalPosition().toPoint().x()
            self._drag_start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)

            cur_x = event.globalPosition().toPoint().x()
            dx = cur_x - self._drag_prev_x
            if abs(dx) > 2:
                if dx > 0 and "run_right" in self._animations:
                    self._set_animation("run_right")
                elif dx < 0 and "run_left" in self._animations:
                    self._set_animation("run_left")
                self._drag_prev_x = cur_x

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            # Check if it was a click (no significant drag)
            if self._drag_start_pos is not None:
                delta = event.globalPosition().toPoint() - self._drag_start_pos
                moved = abs(delta.x()) + abs(delta.y())
                if moved < 5 and self._on_toggle_pause:
                    self._on_toggle_pause()

            self._drag_pos = None
            self._drag_start_pos = None
            self._set_animation(self._pick_animation(self.timer_phase))

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self._on_reset:
                self._on_reset()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.quit_window()

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        W = self.config.width
        H = self.config.height
        P = Theme.PADDING
        R = Theme.CORNER_RADIUS
        is_work = self.timer_phase == "WORK"
        text_color = Theme.TIMER_TEXT_WORK if is_work else Theme.TIMER_TEXT_BREAK

        # --- Background (frosted dark, no border) ---
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(Theme.BG))
        p.drawRoundedRect(QRect(0, 0, W, H), R, R)

        # --- Timer ---
        y = P

        # Timer text
        timer_font = QFont("Helvetica Neue", Theme.FONT_TIMER)
        timer_font.setBold(True)
        p.setFont(timer_font)
        p.setPen(QPen(text_color))
        p.drawText(QRect(0, y, W, Theme.FONT_TIMER + 4), Qt.AlignHCenter, self.timer_text)
        y += Theme.FONT_TIMER + 8

        # Progress bar
        bar_h = 4
        bar_r = bar_h // 2
        bar_rect = QRect(P, y, W - P * 2, bar_h)

        # Track
        p.setBrush(QBrush(Theme.PROGRESS_BG))
        p.drawRoundedRect(bar_rect, bar_r, bar_r)

        # Fill
        fill_w = int((W - P * 2) * self.timer_progress)
        if fill_w > 0:
            grad = QLinearGradient(P, 0, P + fill_w, 0)
            if is_work:
                grad.setColorAt(0, Theme.PROGRESS_WORK_START)
                grad.setColorAt(1, Theme.PROGRESS_WORK_END)
            else:
                grad.setColorAt(0, Theme.PROGRESS_BREAK_START)
                grad.setColorAt(1, Theme.PROGRESS_BREAK_END)
            p.setBrush(QBrush(grad))
            fill_rect = QRect(P, y, fill_w, bar_h)
            p.drawRoundedRect(fill_rect, bar_r, bar_r)

        y += bar_h + 8

        # Phase label + session dots (inline)
        label_font = QFont("Helvetica Neue", Theme.FONT_LABEL)
        label_font.setBold(True)
        p.setFont(label_font)
        p.setPen(QPen(Theme.TEXT_DIM))
        p.drawText(QRect(P, y, 40, 14), Qt.AlignLeft | Qt.AlignVCenter, self.timer_phase)

        # Session dots
        p.setPen(Qt.NoPen)
        dot_x = P + 44
        dot_y = y + 7
        for i in range(8):
            color = Theme.DOT_FILLED if i < self.sessions else Theme.DOT_EMPTY
            p.setBrush(QBrush(color))
            p.drawEllipse(QPoint(dot_x + i * 10, dot_y), 2, 2)

        y += 18

        # --- Pet ---
        frames = self._animations.get(self._current_anim, [])
        if frames and self._frame_index < len(frames):
            frame = frames[self._frame_index]
            pet_x = (W - frame.width()) // 2
            p.drawPixmap(pet_x, y, frame)
            pet_h = frame.height()
        else:
            pet_area = W - P * 2
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(40, 40, 45, 80)))
            p.drawRoundedRect(QRect(P, y, pet_area, pet_area), 16, 16)
            pet_h = pet_area

        y += pet_h + 6

        # Pet name (centered, dim)
        name_font = QFont("Helvetica Neue", 10)
        p.setFont(name_font)
        p.setPen(QPen(Theme.TEXT_DIM))
        p.drawText(QRect(0, y, W, 14), Qt.AlignHCenter, self.pet.display_name)
        y += 16

        # --- Message (bottom, no bar background) ---
        if self.message:
            display_msg = self.message[:32] + ("..." if len(self.message) > 32 else "")
            msg_font = QFont("Helvetica Neue", Theme.FONT_MESSAGE)
            p.setFont(msg_font)
            p.setPen(QPen(Theme.TEXT_SECONDARY))
            slide_offset = int((1.0 - self._message_slide) * 8)
            msg_y = H - P - 16 - slide_offset
            p.drawText(QRect(0, msg_y, W, 16), Qt.AlignHCenter, display_msg)

        # --- Paused overlay ---
        if self.paused:
            # Semi-transparent dim over the whole widget
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(0, 0, 0, 80)))
            p.drawRoundedRect(QRect(0, 0, W, H), R, R)

            # "PAUSED" text centered
            pause_font = QFont("Helvetica Neue", 14)
            pause_font.setBold(True)
            p.setFont(pause_font)
            p.setPen(QPen(QColor(255, 255, 255, 200)))
            p.drawText(QRect(0, H // 2 - 20, W, 30), Qt.AlignHCenter, "⏸  PAUSED")

            # Hint text below
            hint_font = QFont("Helvetica Neue", 9)
            p.setFont(hint_font)
            p.setPen(QPen(QColor(255, 255, 255, 100)))
            p.drawText(QRect(0, H // 2 + 10, W, 20), Qt.AlignHCenter, "click to resume · double-click to reset")

        p.end()
