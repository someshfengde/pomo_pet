"""Pet display window using PySide6 (Qt) — transparent pet-only window."""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Any, List, Dict

from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QBrush

from src.pets.models import AnimationDef
from src.ui.theme import WindowConfig


def _set_window_level_osascript(window_title: str) -> None:
    """Use osascript to set window to float above others."""
    try:
        script = f'''
        tell application "System Events"
            set frontmost of process "{window_title}" to false
        end tell
        '''
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=1)
    except Exception:
        pass


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
        self._idle_timer: float = 0.0
        self._review_toggle: int = 0
        self._review_toggle_timer: float = 0.0
        self._pending_anim: Optional[str] = None

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

    @staticmethod
    def _calc_display_size(sprite_w: int, sprite_h: int) -> tuple[int, int]:
        """Calculate display size: 220px wide, sprite at native size + UI area."""
        window_w = 220
        # Scale sprite to fit within (window_w - 2*margin) with some padding
        max_sprite_w = window_w - 28  # 14px margin each side
        scale = min(max_sprite_w / sprite_w, 1.0)  # never upscale beyond native
        display_sprite_h = int(sprite_h * scale)
        # UI area below sprite: name(16) + timer(30) + progress(8) + label(14) + msg(14) + gaps(40)
        ui_area = 122
        total_h = display_sprite_h + ui_area
        return window_w, total_h

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        sprite_w = self.pet.frame_width
        sprite_h = self.pet.frame_height
        display_w, display_h = self._calc_display_size(sprite_w, sprite_h)
        self._sprite_scale = min((display_w - 28) / sprite_w, 1.0)
        self._sprite_display_w = int(sprite_w * self._sprite_scale)
        self._sprite_display_h = int(sprite_h * self._sprite_scale)
        self.setFixedSize(display_w, display_h)
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
        self._anim_defs = dict(self.pet.animations) if self.pet.animations else {}

        if not self._anim_defs:
            cols = max(sheet.width() // fw, 1)
            rows = max(sheet.height() // fh, 1)
            frames = []
            for r in range(rows):
                for c in range(cols):
                    f = sheet.copy(c * fw, r * fh, fw, fh)
                    frames.append(f)
            self._animations["idle"] = frames
            self._anim_defs["idle"] = AnimationDef(row=0, frames=len(frames), fps=8, loop=True)
            return

        display_w = self._sprite_display_w
        display_h = self._sprite_display_h
        for name, ad in self._anim_defs.items():
            frames = []
            for col in range(ad.frames):
                f = sheet.copy(col * fw, ad.row * fh, fw, fh)
                f = f.scaled(display_w, display_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                frames.append(f)
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_timer_text(self, text: str, phase: str) -> None:
        self.timer_text = text
        self.timer_phase = phase

    def set_timer_progress(self, progress: float) -> None:
        self.timer_progress = max(0.0, min(1.0, progress))

    def set_message(self, message: str) -> None:
        self.message = message

    def set_sessions(self, count: int) -> None:
        self.sessions = count

    def run(self, timer_getter=None, on_toggle_pause=None, on_reset=None) -> None:
        self._timer_getter = timer_getter
        self._on_toggle_pause = on_toggle_pause
        self._on_reset = on_reset
        self.show()
        # WindowStaysOnTopHint keeps it on top — no raise_() needed

    def quit_window(self) -> None:
        QApplication.instance().quit()

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Mouse — drag + gestures
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

    # ------------------------------------------------------------------
    # Paint — uses pet.json metadata for display
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            p.setRenderHint(QPainter.TextAntialiasing)

            W = self.width()
            H = self.height()

            # Clear to fully transparent
            p.setCompositionMode(QPainter.CompositionMode_Source)
            p.fillRect(QRect(0, 0, W, H), QColor(0, 0, 0, 0))
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)

            is_work = self.timer_phase == "WORK"
            timer_color = QColor(52, 199, 89) if is_work else QColor(90, 200, 245)
            dim_color = QColor(140, 140, 148)
            y = 14  # top margin

            # --- Pet name (from pet.json displayName) ---
            name_font = QFont("Helvetica Neue", 11)
            name_font.setBold(True)
            p.setFont(name_font)
            p.setPen(QPen(QColor(220, 220, 224)))
            name_rect = QRect(0, y, W, 16)
            p.drawText(name_rect, Qt.AlignHCenter, self.pet.display_name)
            y += 22

            # --- Pet sprite ---
            frames = self._animations.get(self._current_anim, [])
            sprite_h = 0
            if frames and self._frame_index < len(frames):
                frame = frames[self._frame_index]
                sprite_h = frame.height()
                x = (W - frame.width()) // 2
                p.drawPixmap(x, y, frame)
            y += sprite_h + 10

            # --- Timer text ---
            timer_font = QFont("Helvetica Neue", 22)
            timer_font.setBold(True)
            p.setFont(timer_font)
            p.setPen(QPen(timer_color))
            timer_rect = QRect(0, y, W, 28)
            p.drawText(timer_rect, Qt.AlignHCenter, self.timer_text)
            y += 32

            # --- Progress bar ---
            bar_x = 20
            bar_w = W - 40
            bar_h = 4
            bar_r = bar_h // 2

            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(255, 255, 255, 20)))
            p.drawRoundedRect(QRect(bar_x, y, bar_w, bar_h), bar_r, bar_r)

            fill_w = int(bar_w * self.timer_progress)
            if fill_w > 0:
                p.setBrush(QBrush(timer_color))
                p.drawRoundedRect(QRect(bar_x, y, fill_w, bar_h), bar_r, bar_r)
            y += 12

            # --- Session dots ---
            dot_y = y + 2
            dot_size = 6
            dot_spacing = 12
            max_dots = 4
            dots_x_start = (W - (max_dots * dot_size + (max_dots - 1) * (dot_spacing - dot_size))) // 2
            for i in range(max_dots):
                dx = dots_x_start + i * dot_spacing
                color = QColor(255, 200, 50) if i < self.sessions else QColor(60, 60, 66)
                p.setBrush(QBrush(color))
                p.setPen(Qt.NoPen)
                p.drawEllipse(dx, dot_y, dot_size, dot_size)
            y += 14

            # --- Animation state label ---
            anim_label = self._current_anim.replace("_", " ").title()
            ad = self._anim_defs.get(self._current_anim)
            if ad:
                anim_info = f"{anim_label} · {ad.fps}fps"
            else:
                anim_info = anim_label

            anim_font = QFont("Helvetica Neue", 8)
            p.setFont(anim_font)
            p.setPen(QPen(QColor(100, 100, 108)))
            anim_rect = QRect(0, y, W, 12)
            p.drawText(anim_rect, Qt.AlignHCenter, anim_info)
            y += 16

            # --- Message ---
            if self.message:
                display_msg = self.message[:28] + ("..." if len(self.message) > 28 else "")
                msg_font = QFont("Helvetica Neue", 9)
                p.setFont(msg_font)
                p.setPen(QPen(dim_color))
                msg_rect = QRect(0, y, W, 14)
                p.drawText(msg_rect, Qt.AlignHCenter, display_msg)

        finally:
            p.end()
