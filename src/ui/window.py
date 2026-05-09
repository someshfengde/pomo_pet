"""Pet display window using PySide6 (Qt)."""

import math
from pathlib import Path
from typing import Optional, Any, List, Dict

from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import (
    QPainter, QColor, QPixmap, QFont, QPen, QBrush, QLinearGradient,
)

from src.pets.models import AnimationDef
from src.ui.theme import Theme, WindowConfig


class PetWindow(QMainWindow):

    def __init__(self, pet: Any, config: Optional[WindowConfig] = None, parent=None) -> None:
        super().__init__(parent)
        self.pet = pet
        self.config = config or WindowConfig()

        self.timer_text: str = "25:00"
        self.timer_phase: str = "WORK"
        self.timer_progress: float = 0.0
        self.message: str = "Let's focus!"
        self.sessions: int = 0
        self.paused: bool = False

        self._animations: Dict[str, List[QPixmap]] = {}
        self._anim_defs: Dict[str, AnimationDef] = {}
        self._current_anim: str = "idle"
        self._frame_index: int = 0
        self._frame_timer: float = 0.0
        self._message_slide: float = 0.0
        self._idle_timer: float = 0.0
        self._review_toggle: int = 0
        self._review_toggle_timer: float = 0.0
        self._pending_anim: Optional[str] = None

        self._drag_pos: Optional[QPoint] = None
        self._drag_prev_x: int = 0
        self._drag_start_pos: Optional[QPoint] = None

        self._timer_getter = None
        self._on_toggle_pause = None
        self._on_reset = None
        self._last_phase: Optional[str] = None

        self._setup_window()
        self._load_animations()
        self._setup_timer()

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setFixedSize(self.config.width, self.config.height)
        self.move(100, 100)

        # Periodically raise window to keep it on top (macOS workaround)
        self._raise_timer = QTimer(self)
        self._raise_timer.timeout.connect(self.raise_)
        self._raise_timer.start(2000)  # every 2 seconds

    def _setup_timer(self) -> None:
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(1000 // self.config.fps)

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
        if self._pending_anim:
            return
        if name == self._current_anim or name not in self._animations:
            return
        self._current_anim = name
        self._frame_index = 0
        self._frame_timer = 0.0

    def _play_once(self, name: str) -> None:
        if self._pending_anim:
            return
        if name not in self._animations:
            return
        self._pending_anim = self._pick_animation(self.timer_phase)
        self._current_anim = name
        self._frame_index = 0
        self._frame_timer = 0.0

    def _pick_animation(self, phase: str) -> str:
        phase = phase.upper()
        if phase == "WORK":
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

    def _tick(self) -> None:
        dt = 1.0 / self.config.fps
        triggered = False

        if self._timer_getter is not None:
            remaining, phase, sessions, message, progress, paused = self._timer_getter()

            if remaining == "00:00" and not paused and not triggered:
                self._play_once("failed")
                triggered = True
            if not triggered and sessions > self.sessions and self.sessions > 0:
                self._play_once("waving")
                triggered = True
            if not triggered and phase != self.timer_phase and self._last_phase is not None:
                self._play_once("jumping")
                triggered = True

            self.set_timer_text(remaining, phase)
            self.set_sessions(sessions)
            self.set_timer_progress(progress)
            self.paused = paused
            if message:
                self.set_message(message)

        if self.timer_phase != self._last_phase:
            self._last_phase = self.timer_phase
            self._review_toggle = 0
            self._review_toggle_timer = 0.0
            if not self._pending_anim:
                self._set_animation(self._pick_animation(self.timer_phase))

        if self._current_anim == "idle" and not self._pending_anim:
            self._idle_timer += dt
            if self._idle_timer >= 30.0 and "waiting" in self._animations:
                self._set_animation("waiting")
                self._idle_timer = 0.0
        elif self._current_anim != "waiting":
            self._idle_timer = 0.0

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
                        next_anim = self._pending_anim
                        self._pending_anim = None
                        self._current_anim = next_anim
                        self._frame_index = 0
                        self._frame_timer = 0.0
                    elif ad and ad.loop:
                        self._frame_index = 0
                    else:
                        target = self._pick_animation(self.timer_phase)
                        self._current_anim = target
                        self._frame_index = 0
                        self._frame_timer = 0.0

        if self._message_slide < 1.0:
            self._message_slide = min(1.0, self._message_slide + dt * 3.0)

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
            if self._drag_start_pos is not None:
                delta = event.globalPosition().toPoint() - self._drag_start_pos
                moved = abs(delta.x()) + abs(delta.y())
                if moved < 5 and self._on_toggle_pause:
                    self._on_toggle_pause()
            self._drag_pos = None
            self._drag_start_pos = None
            if not self._pending_anim:
                self._set_animation(self._pick_animation(self.timer_phase))

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self._on_reset:
                self._on_reset()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.quit_window()

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

        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(QRect(0, 0, W, H), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(Theme.BG))
        p.drawRoundedRect(QRect(0, 0, W, H), R, R)

        y = P
        timer_font = QFont("Helvetica Neue", Theme.FONT_TIMER)
        timer_font.setBold(True)
        p.setFont(timer_font)
        p.setPen(QPen(text_color))
        p.drawText(QRect(0, y, W, Theme.FONT_TIMER + 4), Qt.AlignHCenter, self.timer_text)
        y += Theme.FONT_TIMER + 8

        bar_h = 4
        bar_r = bar_h // 2
        p.setBrush(QBrush(Theme.PROGRESS_BG))
        p.drawRoundedRect(QRect(P, y, W - P * 2, bar_h), bar_r, bar_r)

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
            p.drawRoundedRect(QRect(P, y, fill_w, bar_h), bar_r, bar_r)

        y += bar_h + 8

        label_font = QFont("Helvetica Neue", Theme.FONT_LABEL)
        label_font.setBold(True)
        p.setFont(label_font)
        p.setPen(QPen(Theme.TEXT_DIM))
        p.drawText(QRect(P, y, 40, 14), Qt.AlignLeft | Qt.AlignVCenter, self.timer_phase)

        p.setPen(Qt.NoPen)
        dot_x = P + 44
        dot_y = y + 7
        for i in range(8):
            color = Theme.DOT_FILLED if i < self.sessions else Theme.DOT_EMPTY
            p.setBrush(QBrush(color))
            p.drawEllipse(QPoint(dot_x + i * 10, dot_y), 2, 2)

        y += 18

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

        name_font = QFont("Helvetica Neue", 10)
        p.setFont(name_font)
        p.setPen(QPen(Theme.TEXT_DIM))
        p.drawText(QRect(0, y, W, 14), Qt.AlignHCenter, self.pet.display_name)

        if self.message:
            display_msg = self.message[:32] + ("..." if len(self.message) > 32 else "")
            msg_font = QFont("Helvetica Neue", Theme.FONT_MESSAGE)
            p.setFont(msg_font)
            p.setPen(QPen(Theme.TEXT_SECONDARY))
            slide_offset = int((1.0 - self._message_slide) * 8)
            msg_y = H - P - 16 - slide_offset
            p.drawText(QRect(0, msg_y, W, 16), Qt.AlignHCenter, display_msg)

        if self.paused:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(0, 0, 0, 60)))
            p.drawRoundedRect(QRect(0, 0, W, H), R, R)

            pause_font = QFont("Helvetica Neue", 14)
            pause_font.setBold(True)
            p.setFont(pause_font)
            p.setPen(QPen(QColor(255, 255, 255, 200)))
            p.drawText(QRect(0, H // 2 - 20, W, 30), Qt.AlignHCenter, "PAUSED")

            hint_font = QFont("Helvetica Neue", 9)
            p.setFont(hint_font)
            p.setPen(QPen(QColor(255, 255, 255, 100)))
            p.drawText(QRect(0, H // 2 + 10, W, 20), Qt.AlignHCenter, "click to resume / double-click to reset")

        p.end()
