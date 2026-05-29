"""Pet display window using PySide6 (Qt) — transparent pet-only window."""

import sys
from pathlib import Path
from typing import Optional, Any, List, Dict

from PySide6.QtWidgets import QMainWindow, QApplication, QMenu
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QBrush, QShortcut, QKeySequence, QAction, QCursor

from src.pets.models import AnimationDef
from src.ui.theme import WindowConfig, Theme

# macOS: load AppKit for native window control (pyobjc handles ARM64 ABI correctly)
_AppKit = None
if sys.platform == "darwin":
    try:
        import AppKit
        _AppKit = AppKit
    except Exception:
        pass


# ---------------------------------------------------------------------------
# PetWindow
# ---------------------------------------------------------------------------

class PetWindow(QMainWindow):

    def __init__(self, pet: Any, config: Optional[WindowConfig] = None,
                 pomo_config: Any = None, parent=None) -> None:
        super().__init__(parent)
        self.pet = pet
        self.config = config or WindowConfig()
        self._pomo_config = pomo_config  # persistent config for saving window position

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
        self._on_skip = None
        self._last_phase: Optional[str] = None

        self._setup_window()
        self._load_animations()
        self._setup_timer()
        self._setup_shortcuts()

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
        self.setWindowTitle(self.pet.display_name)
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

        # Restore saved position or use default
        if self._pomo_config and self._pomo_config.window_x is not None and self._pomo_config.window_y is not None:
            x, y = self._pomo_config.window_x, self._pomo_config.window_y
            # Ensure the window is visible on at least one screen
            on_screen = False
            for screen in QApplication.screens():
                if screen.geometry().contains(x, y):
                    on_screen = True
                    break
            if on_screen:
                self.move(x, y)
            else:
                self.move(100, 100)
        else:
            self.move(100, 100)

    def _apply_floating_level(self) -> None:
        """Apply NSFloatingWindowLevel to the real NSWindow.

        Must be called AFTER show() so winId() returns a valid native handle.
        Uses pyobjc AppKit — handles ARM64 calling convention correctly.
        """
        if _AppKit is None or sys.platform != "darwin":
            return

        try:
            ns_view_ptr = int(self.winId())
            if ns_view_ptr == 0:
                return

            # Convert the raw pointer to an ObjC object (cached on first call)
            if not hasattr(self, '_pyobjc_new'):
                from ctypes import c_void_p, py_object, pythonapi
                pythonapi.PyObjCObject_New.restype = py_object
                pythonapi.PyObjCObject_New.argtypes = [c_void_p, c_void_p, c_void_p]
                self._pyobjc_new = pythonapi.PyObjCObject_New
                self._c_void_p = c_void_p

            ns_view = self._pyobjc_new(self._c_void_p(ns_view_ptr), 0, 0)

            # winId() returns the NSView — get the NSWindow from it
            ns_window = ns_view.window()
            if ns_window is None:
                return

            # Use NSFloatingWindowLevel (3) — stays above normal windows
            # but below system UI.  Re-applied periodically so macOS cannot
            # silently drop the level after focus changes or Space switches.
            ns_window.setLevel_(_AppKit.NSFloatingWindowLevel)
            ns_window.setHidesOnDeactivate_(False)

            # Make the window appear on ALL Spaces/Desktops so it never
            # disappears when the user switches to a different Space.
            # NSWindowCollectionBehaviorCanJoinAllSpaces = 1 << 0
            # NSWindowCollectionBehaviorStationary = 1 << 1
            # Combined = 3
            ns_window.setCollectionBehavior_(1 | 2)  # CanJoinAllSpaces | Stationary

            # Ensure the window is ordered to the front of its level.
            # This is more reliable than Qt's raise_() because it operates
            # at the native window server level.
            ns_window.orderFrontRegardless()

            # Ensure the window is visible (not miniaturized/hidden).
            if ns_window.isMiniaturized():
                ns_window.deminiaturize_(None)
            if not ns_window.isVisible():
                ns_window.makeKeyAndOrderFront_(None)

        except Exception:
            pass  # graceful fallback

    def _on_app_state_changed(self, state) -> None:
        """Re-apply floating level when application state changes."""
        # Qt.ApplicationActive = 4, Qt.ApplicationInactive = 2
        # Re-apply in both cases to be safe — the call is cheap.
        QTimer.singleShot(0, self._apply_floating_level)
        # Also re-apply after a short delay to catch race conditions
        # where macOS re-orders windows after the state change completes.
        QTimer.singleShot(300, self._apply_floating_level)

    def _save_position(self) -> None:
        """Save current window position to persistent config."""
        if self._pomo_config is not None:
            pos = self.pos()
            self._pomo_config.update(window_x=pos.x(), window_y=pos.y())

    def _nudge(self, dx: int, dy: int) -> None:
        """Move window by a small delta (keyboard nudge)."""
        pos = self.pos()
        self.move(pos.x() + dx, pos.y() + dy)
        self._save_position()

    def _reset_position(self) -> None:
        """Move window to center-top of primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + 100
            self.move(x, y)
            self._save_position()

    def _move_to(self, position: str) -> None:
        """Move window to a predefined screen position."""
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        margin = 20
        w, h = self.width(), self.height()

        if position == "top_left":
            x, y = geo.x() + margin, geo.y() + margin
        elif position == "top_right":
            x, y = geo.x() + geo.width() - w - margin, geo.y() + margin
        elif position == "bottom_left":
            x, y = geo.x() + margin, geo.y() + geo.height() - h - margin
        elif position == "bottom_right":
            x, y = geo.x() + geo.width() - w - margin, geo.y() + geo.height() - h - margin
        elif position == "center":
            x = geo.x() + (geo.width() - w) // 2
            y = geo.y() + (geo.height() - h) // 2
        else:
            return

        self.move(x, y)
        self._save_position()

    def _setup_timer(self) -> None:
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(1000 // self.config.fps)

    def _setup_shortcuts(self) -> None:
        """Global keyboard shortcuts — Cmd+Shift+P/R/Q on macOS."""
        # Pause / Resume
        sc_pause = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        sc_pause.activated.connect(self._shortcut_toggle_pause)

        # Reset
        sc_reset = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        sc_reset.activated.connect(self._shortcut_reset)

        # Quit
        sc_quit = QShortcut(QKeySequence("Ctrl+Shift+Q"), self)
        sc_quit.activated.connect(self.quit_window)

        # Nudge window with arrow keys (Ctrl+Arrow = Cmd+Arrow on macOS)
        for key, dx, dy in [
            (Qt.Key_Up, 0, -20), (Qt.Key_Down, 0, 20),
            (Qt.Key_Left, -20, 0), (Qt.Key_Right, 20, 0),
        ]:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda d=(dx, dy): self._nudge(*d))

    def _shortcut_toggle_pause(self) -> None:
        if self._on_toggle_pause:
            self._on_toggle_pause()

    def _shortcut_reset(self) -> None:
        if self._on_reset:
            self._on_reset()

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
            # BREAK and LONG_BREAK both use idle/relaxed animations
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

    def run(self, timer_getter=None, on_toggle_pause=None, on_reset=None,
            on_skip=None) -> None:
        self._timer_getter = timer_getter
        self._on_toggle_pause = on_toggle_pause
        self._on_reset = on_reset
        self._on_skip = on_skip
        self.show()
        # Apply native floating level AFTER show() — winId() is valid now
        # Use a timer to ensure the native window is fully created
        QTimer.singleShot(0, self._apply_floating_level)

        # Periodically re-apply the floating level so macOS cannot silently
        # drop it after focus changes, Space switches, or fullscreen exits.
        self._float_timer = QTimer(self)
        self._float_timer.timeout.connect(self._apply_floating_level)
        self._float_timer.start(2000)  # every 2 seconds

        # Re-apply immediately when the application state changes (e.g. user
        # switches to another app and back).
        app = QApplication.instance()
        if app is not None:
            app.applicationStateChanged.connect(self._on_app_state_changed)

        # Also re-apply when the screen changes (Space switch, display connect).
        # screenChanged lives on QWindow, which we reach via QWidget.windowHandle().
        wh = self.windowHandle()
        if wh is not None:
            wh.screenChanged.connect(lambda _: QTimer.singleShot(100, self._apply_floating_level))

    def _show_context_menu(self) -> None:
        """Show a right-click context menu with timer controls."""
        menu = QMenu(self)
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
            QMenu::item:disabled {
                color: rgba(255, 255, 255, 160);
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 10);
                margin: 4px 8px;
            }
        """)

        # Timer status header
        phase_emoji = {"WORK": "🔴", "BREAK": "🟢", "LONG_BREAK": "🟣"}.get(self.timer_phase, "⚪")
        status_text = f"{phase_emoji}  {self.timer_text}  ·  {self.timer_phase.replace('_', ' ').title()}"
        status_action = QAction(status_text, self)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        menu.addSeparator()

        # Pause / Resume
        pause_text = "▶  Resume" if self.paused else "⏸  Pause"
        pause_action = QAction(pause_text, self)
        pause_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        pause_action.triggered.connect(self._shortcut_toggle_pause)
        menu.addAction(pause_action)

        # Reset
        reset_action = QAction("↺  Reset Timer", self)
        reset_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        reset_action.triggered.connect(self._shortcut_reset)
        menu.addAction(reset_action)

        # Skip phase
        if self._on_skip:
            skip_action = QAction("⏭  Skip Phase", self)
            skip_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
            skip_action.triggered.connect(self._on_skip)
            menu.addAction(skip_action)

        menu.addSeparator()

        # Reset Position
        reset_pos_action = QAction("📍  Reset Position", self)
        reset_pos_action.triggered.connect(self._reset_position)
        menu.addAction(reset_pos_action)

        # Move to submenu
        move_menu = menu.addMenu("📌  Move to")
        positions = [
            ("↖  Top Left", "top_left"),
            ("↗  Top Right", "top_right"),
            ("↙  Bottom Left", "bottom_left"),
            ("↘  Bottom Right", "bottom_right"),
            ("⊙  Center", "center"),
        ]
        for label, pos_id in positions:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, p=pos_id: self._move_to(p))
            move_menu.addAction(action)

        menu.addSeparator()

        # Quit
        quit_action = QAction("✕  Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Shift+Q"))
        quit_action.triggered.connect(self.quit_window)
        menu.addAction(quit_action)

        menu.exec(QCursor.pos())

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
        if event.button() == Qt.RightButton:
            self._show_context_menu()
            return
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
                elif moved >= 5:
                    # Save window position after drag
                    self._save_position()
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

    def showEvent(self, event) -> None:
        """Re-apply floating level when window is shown."""
        super().showEvent(event)
        QTimer.singleShot(0, self._apply_floating_level)

    def enterEvent(self, event) -> None:
        """Mouse enters window — play waving animation."""
        if "waving" in self._animations and not self._pending_anim:
            self._play_once("waving")
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Mouse leaves window — return to phase-appropriate animation."""
        if not self._pending_anim:
            self._set_animation(self._pick_animation(self.timer_phase))
        super().leaveEvent(event)

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

            # Phase-aware colors from Theme
            if self.timer_phase == "WORK":
                timer_color = Theme.TIMER_TEXT_WORK
            elif self.timer_phase == "LONG_BREAK":
                timer_color = QColor(190, 140, 255)  # purple for long breaks
            else:
                timer_color = Theme.TIMER_TEXT_BREAK
            dim_color = Theme.TEXT_SECONDARY
            y = 14  # top margin

            # --- Pet name (from pet.json displayName) ---
            name_font = QFont("Helvetica Neue", 11)
            name_font.setBold(True)
            p.setFont(name_font)
            p.setPen(QPen(Theme.TEXT_PRIMARY))
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

            # --- Subtle backdrop behind UI text area ---
            # A rounded dark translucent pill so the timer/dots/message
            # stay readable against any desktop wallpaper.
            ui_top = y - 6
            ui_bottom = H - 6
            pill_margin = 10
            pill_rect = QRect(pill_margin, ui_top, W - 2 * pill_margin, ui_bottom - ui_top)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(0, 0, 0, 90)))
            p.drawRoundedRect(pill_rect, 10, 10)

            # --- Timer text ---
            timer_font = QFont("Helvetica Neue", 22)
            timer_font.setBold(True)
            p.setFont(timer_font)
            p.setPen(QPen(timer_color))
            timer_rect = QRect(0, y, W, 28)
            p.drawText(timer_rect, Qt.AlignHCenter, self.timer_text)
            y += 32

            # --- Progress bar ---
            bar_x = 28
            bar_w = W - 56
            bar_h = 4
            bar_r = bar_h // 2

            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(Theme.PROGRESS_BG))
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
                color = Theme.DOT_FILLED if i < self.sessions else Theme.DOT_EMPTY
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
            p.setPen(QPen(Theme.TEXT_DIM))
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
