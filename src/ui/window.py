"""Pet display window using PySide6 (Qt) — transparent pet-only window."""

import ctypes
import ctypes.util
import math
import sys
from pathlib import Path
from typing import Optional, Any, List, Dict

from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPainter, QPixmap, QColor

from src.pets.models import AnimationDef
from src.ui.theme import WindowConfig


# ---------------------------------------------------------------------------
# macOS NSWindow helpers
# ---------------------------------------------------------------------------

_objc = None

def _get_objc():
    global _objc
    if _objc is None:
        lib_path = ctypes.util.find_library("objc")
        if lib_path:
            _objc = ctypes.CDLL(lib_path)
    return _objc

def _sel(name: str) -> int:
    objc = _get_objc()
    if not objc:
        return 0
    objc.sel_registerName.restype = ctypes.c_void_p
    objc.sel_registerName.argtypes = [ctypes.c_char_p]
    return objc.sel_registerName(name.encode())

def _msg(obj: int, sel: int, *args):
    objc = _get_objc()
    if not objc:
        return 0
    objc.objc_msgSend.restype = ctypes.c_void_p
    objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p] + [type(a) for a in args]
    return objc.objc_msgSend(obj, sel, *args)

def _set_nswindow_level(window_id: int, level: int) -> None:
    try:
        _msg(window_id, _sel("setLevel:"), level)
    except Exception:
        pass

def _set_nswindow_opaque(window_id: int, opaque: bool) -> None:
    try:
        _msg(window_id, _sel("setOpaque:"), 1 if opaque else 0)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# PetWindow — transparent, pet-only
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
        self.message: str = ""
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
    def _calc_scale(sprite_w: int, sprite_h: int) -> int:
        """Calculate optimal scale factor for display.

        Target: ~150-200px on the larger dimension.
        - 64px sprite  → 2x = 128px
        - 96px sprite  → 2x = 192px
        - 128px sprite → 1x = 128px
        - 192px sprite → 1x = 192px
        - 256px sprite → 1x = 256px
        """
        max_dim = max(sprite_w, sprite_h)
        if max_dim <= 100:
            return 2
        else:
            return 1

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        # Intelligent sizing: scale sprite to a good display size
        sprite_w = self.pet.frame_width
        sprite_h = self.pet.frame_height
        scale = self._calc_scale(sprite_w, sprite_h)
        self._sprite_scale = scale
        self.setFixedSize(sprite_w * scale, sprite_h * scale)
        self.move(100, 100)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if sys.platform == "darwin":
            try:
                nswindow_ptr = int(self.winId())
                _set_nswindow_level(nswindow_ptr, 3)  # NSFloatingWindowLevel
                _set_nswindow_opaque(nswindow_ptr, False)
            except Exception:
                pass

    def _setup_timer(self) -> None:
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(1000 // self.config.fps)

    # ------------------------------------------------------------------
    # Animations — load from pet.json
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
            # Fallback: treat as single idle animation
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

        # Load each animation and scale to display size
        display_w = self.pet.frame_width * self._sprite_scale
        display_h = self.pet.frame_height * self._sprite_scale
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
            fps = ad.fps if ad else 8  # fps from pet.json
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
    # Paint — ONLY the pet sprite, fully transparent background
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Use actual window size, not config
        W = self.width()
        H = self.height()

        # Clear to fully transparent
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(QRect(0, 0, W, H), QColor(0, 0, 0, 0))
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Draw only the current animation frame
        frames = self._animations.get(self._current_anim, [])
        if frames and self._frame_index < len(frames):
            frame = frames[self._frame_index]
            x = (W - frame.width()) // 2
            y = (H - frame.height()) // 2
            p.drawPixmap(x, y, frame)

        p.end()
