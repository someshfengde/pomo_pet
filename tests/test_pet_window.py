"""Tests for the PySide6 pet display window."""

import sys
import pytest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from src.ui.window import PetWindow
from src.ui.theme import Theme, WindowConfig
from src.pets.models import AnimationDef, Pet
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QMouseEvent


@pytest.fixture
def spritesheet(tmp_path):
    from PIL import Image
    img = Image.new("RGBA", (192 * 8, 192 * 9), (100, 200, 100, 255))
    path = tmp_path / "spritesheet.webp"
    img.save(path, "WEBP")
    return str(path)


@pytest.fixture
def test_pet(spritesheet):
    return Pet(
        id="test", display_name="TestPet", description="A test pet.",
        spritesheet_path=spritesheet, kind="creature",
        frame_width=192, frame_height=192,
        animations={
            "idle": AnimationDef(row=0, frames=6, fps=8, loop=True),
            "run_right": AnimationDef(row=1, frames=8, fps=12, loop=True),
            "run_left": AnimationDef(row=2, frames=8, fps=12, loop=True),
            "waving": AnimationDef(row=3, frames=4, fps=8, loop=False),
            "jumping": AnimationDef(row=4, frames=5, fps=10, loop=False),
            "failed": AnimationDef(row=5, frames=8, fps=10, loop=False),
            "waiting": AnimationDef(row=6, frames=6, fps=6, loop=True),
            "running": AnimationDef(row=7, frames=6, fps=10, loop=True),
            "review": AnimationDef(row=8, frames=6, fps=8, loop=True),
        },
    )


@pytest.fixture
def window(test_pet):
    w = PetWindow(pet=test_pet)
    yield w
    w.close()


def _press(x, y):
    return QMouseEvent(QMouseEvent.MouseButtonPress, QPointF(x, y), QPointF(x, y),
                       Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)


def _move(x, y):
    return QMouseEvent(QMouseEvent.MouseMove, QPointF(x, y), QPointF(x, y),
                       Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)


def _release(x, y):
    return QMouseEvent(QMouseEvent.MouseButtonRelease, QPointF(x, y), QPointF(x, y),
                       Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)


def _dblclick(x, y):
    return QMouseEvent(QMouseEvent.MouseButtonDblClick, QPointF(x, y), QPointF(x, y),
                       Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)


class TestWindowConfig:
    def test_default(self):
        c = WindowConfig()
        assert c.width == Theme.WIDTH
        assert c.height == Theme.HEIGHT


class TestPetWindowInit:
    def test_initial_state(self, window):
        assert window._drag_pos is None
        assert window.timer_text == "25:00"
        assert window.paused is False
        assert window._current_anim == "idle"
        assert window._pending_anim is None
        assert window._idle_timer == 0.0


class TestAnimationSystem:
    def test_all_loaded(self, window):
        for name in ("idle", "run_right", "run_left", "waving", "jumping",
                      "failed", "waiting", "running", "review"):
            assert name in window._animations, f"{name} not loaded"

    def test_frame_counts(self, window):
        assert len(window._animations["idle"]) == 6
        assert len(window._animations["waving"]) == 4
        assert len(window._animations["jumping"]) == 5
        assert len(window._animations["failed"]) == 8
        assert len(window._animations["review"]) == 6

    def test_set_animation(self, window):
        window._set_animation("running")
        assert window._current_anim == "running"
        assert window._frame_index == 0

    def test_pick_work_prefers_running(self, window):
        window._review_toggle = 0
        assert window._pick_animation("WORK") == "running"

    def test_pick_work_alternates_review(self, window):
        window._review_toggle = 1
        assert window._pick_animation("WORK") == "review"

    def test_pick_break_prefers_idle(self, window):
        assert window._pick_animation("BREAK") == "idle"

    def test_animate_advances(self, window):
        window._current_anim = "idle"
        window._frame_index = 0
        window._frame_timer = 0.0
        window._animate(0.13)
        assert window._frame_index == 1

    def test_animate_loops(self, window):
        window._current_anim = "idle"
        window._frame_index = 5
        window._frame_timer = 0.0
        window._animate(0.13)
        assert window._frame_index == 0


class TestPlayOnce:
    """Test one-shot animation system."""

    def test_play_once_sets_pending(self, window):
        """_play_once stores the return animation."""
        window._current_anim = "idle"
        window.timer_phase = "WORK"
        window._play_once("waving")
        assert window._current_anim == "waving"
        assert window._pending_anim == "running"

    def test_play_once_returns_to_pending(self, window):
        """After one-shot finishes, returns to pending animation."""
        window._current_anim = "waving"
        window._pending_anim = "running"
        window._frame_index = 3  # last frame of waving (4 frames)
        window._frame_timer = 0.0
        window._animate(0.13)
        assert window._current_anim == "running"
        assert window._pending_anim is None

    def test_play_once_unknown_ignored(self, window):
        """_play_once with unknown animation is a no-op."""
        window._current_anim = "idle"
        window._play_once("nonexistent")
        assert window._current_anim == "idle"

    def test_play_once_skips_if_already_pending(self, window):
        """Don't override an already-pending one-shot."""
        window._pending_anim = "idle"
        window._current_anim = "waving"
        window._play_once("jumping")
        assert window._current_anim == "waving"  # unchanged
        assert window._pending_anim == "idle"  # unchanged


class TestTriggerSessionComplete:
    """Test waving triggers on session complete."""

    def test_waving_on_session_complete(self, window):
        """Sessions increasing triggers waving."""
        window.sessions = 1
        window._timer_getter = lambda: ("25:00", "WORK", 2, "Done!", 1.0, False)
        window._tick()
        assert window._current_anim == "waving"

    def test_no_waving_on_first_session(self, window):
        """Don't wave on the very first session (sessions goes 0->1)."""
        window.sessions = 0
        window._timer_getter = lambda: ("25:00", "BREAK", 1, "Break!", 0.0, False)
        window._tick()
        assert window._current_anim != "waving"


class TestTriggerPhaseTransition:
    """Test jumping triggers on phase transition."""

    def test_jumping_on_phase_change(self, window):
        """Phase change triggers jumping."""
        window.timer_phase = "WORK"
        window._last_phase = "WORK"
        window._timer_getter = lambda: ("05:00", "BREAK", 1, "Break!", 1.0, False)
        window._tick()
        assert window._current_anim == "jumping"

    def test_no_jump_if_pending(self, window):
        """Don't jump if a one-shot is already pending."""
        window.timer_phase = "WORK"
        window._last_phase = "WORK"
        window._pending_anim = "idle"
        window._timer_getter = lambda: ("05:00", "BREAK", 1, "Break!", 1.0, False)
        window._tick()
        assert window._current_anim != "jumping"


class TestTriggerTimerExpire:
    """Test failed triggers when timer hits 00:00."""

    def test_failed_on_expire(self, window):
        """Timer at 00:00 triggers failed animation."""
        window._timer_getter = lambda: ("00:00", "WORK", 0, "Time!", 0.0, False)
        window._tick()
        assert window._current_anim == "failed"

    def test_no_failed_when_paused(self, window):
        """Don't trigger failed when paused."""
        window._timer_getter = lambda: ("00:00", "WORK", 0, "Time!", 0.0, True)
        window._tick()
        assert window._current_anim != "failed"

    def test_no_failed_if_pending(self, window):
        """Don't trigger failed if one-shot pending."""
        window._pending_anim = "idle"
        window._timer_getter = lambda: ("00:00", "WORK", 0, "Time!", 0.0, False)
        window._tick()
        assert window._current_anim != "failed"


class TestTriggerIdleWaiting:
    """Test waiting triggers after long idle."""

    def test_waiting_after_30s_idle(self, window):
        """After 30 seconds of idle, switches to waiting."""
        window._current_anim = "idle"
        window._idle_timer = 30.0  # already at threshold
        window._timer_getter = lambda: ("25:00", "BREAK", 0, "Rest!", 1.0, False)
        window._tick()
        assert window._current_anim == "waiting"
        assert window._idle_timer == 0.0

    def test_idle_timer_resets_on_non_idle(self, window):
        """Idle timer resets when not in idle animation."""
        window._current_anim = "running"
        window._idle_timer = 20.0
        window._timer_getter = lambda: ("25:00", "WORK", 0, "Focus!", 0.5, False)
        window._tick()
        assert window._idle_timer == 0.0


class TestTriggerReviewAlternation:
    """Test running/review alternate during work phase."""

    def test_review_toggle_advances(self, window):
        """Review toggle increments after 10 seconds."""
        window._current_anim = "running"
        window._review_toggle = 0
        window._review_toggle_timer = 10.0
        window._last_phase = "WORK"  # avoid phase change reset
        window._timer_getter = lambda: ("25:00", "WORK", 0, "Focus!", 0.5, False)
        window._tick()
        assert window._review_toggle == 1
        assert window._current_anim == "review"


class TestDragDirection:
    def test_drag_right(self, window):
        window._current_anim = "idle"
        window.mousePressEvent(_press(100, 100))
        window.mouseMoveEvent(_move(150, 100))
        assert window._current_anim == "run_right"

    def test_drag_left(self, window):
        window._current_anim = "idle"
        window.mousePressEvent(_press(100, 100))
        window.mouseMoveEvent(_move(50, 100))
        assert window._current_anim == "run_left"

    def test_release_returns_to_phase(self, window):
        window._current_anim = "run_right"
        window.timer_phase = "WORK"
        window._drag_pos = QPoint(0, 0)
        window._drag_start_pos = QPoint(100, 100)
        window.mouseReleaseEvent(_release(100, 100))
        assert window._current_anim == "running"


class TestClickPause:
    def test_click_toggles_pause(self, window):
        called = []
        window._on_toggle_pause = lambda: called.append(True)
        window.mousePressEvent(_press(100, 100))
        window.mouseReleaseEvent(_release(100, 100))
        assert called == [True]

    def test_drag_no_toggle(self, window):
        called = []
        window._on_toggle_pause = lambda: called.append(True)
        window.mousePressEvent(_press(100, 100))
        window.mouseMoveEvent(_move(200, 100))
        window.mouseReleaseEvent(_release(200, 100))
        assert called == []


class TestDoubleClickReset:
    def test_double_click_resets(self, window):
        called = []
        window._on_reset = lambda: called.append(True)
        window.mouseDoubleClickEvent(_dblclick(100, 100))
        assert called == [True]


class TestStatusDisplay:
    def test_progress_clamped(self, window):
        window.set_timer_progress(1.5)
        assert window.timer_progress == 1.0


class TestRun:
    def test_sets_callbacks(self, window):
        g = lambda: ("10:00", "WORK", 0, "hi", 0.5, False)
        window.run(timer_getter=g, on_toggle_pause=lambda: None, on_reset=lambda: None)
        assert window._timer_getter is g

    def test_tick_calls_getter(self, window):
        window._timer_getter = lambda: ("10:00", "BREAK", 3, "Rest!", 0.25, False)
        window._tick()
        assert window.timer_text == "10:00"
        assert window.paused is False
