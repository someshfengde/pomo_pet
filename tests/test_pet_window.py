"""Tests for the PySide6 pet display window."""

import sys
import pytest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from src.ui.window import PetWindow
from src.ui.theme import WindowConfig
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


class TestWindowSetup:
    def test_window_size_matches_sprite(self, window):
        """Window uses frameWidth/frameHeight from pet.json."""
        assert window.width() == 192
        assert window.height() == 192

    def test_initial_state(self, window):
        assert window._current_anim == "idle"
        assert window._pending_anim is None

    def test_translucent_background(self, window):
        assert window.testAttribute(Qt.WA_TranslucentBackground)


class TestAnimationSystem:
    def test_all_loaded(self, window):
        for name in ("idle", "run_right", "run_left", "waving", "jumping",
                      "failed", "waiting", "running", "review"):
            assert name in window._animations

    def test_frame_count(self, window):
        assert len(window._animations["idle"]) == 6
        assert len(run_right := window._animations["run_right"]) == 8

    def test_frames_are_native_size(self, window):
        """Frames are native size from pet.json (no scaling)."""
        frame = window._animations["idle"][0]
        assert frame.width() == 192
        assert frame.height() == 192

    def test_fps_from_pet_json(self, window):
        """Animation fps comes from pet.json."""
        assert window._anim_defs["idle"].fps == 8
        assert window._anim_defs["run_right"].fps == 12
        assert window._anim_defs["waiting"].fps == 6

    def test_set_animation(self, window):
        window._set_animation("running")
        assert window._current_anim == "running"

    def test_set_animation_blocked_during_oneshot(self, window):
        window._pending_anim = "idle"
        window._current_anim = "waving"
        window._set_animation("running")
        assert window._current_anim == "waving"

    def test_pick_work(self, window):
        window._review_toggle = 0
        assert window._pick_animation("WORK") == "running"

    def test_pick_break(self, window):
        assert window._pick_animation("BREAK") == "idle"

    def test_animate_uses_pet_json_fps(self, window):
        """Frame advances at the rate specified in pet.json."""
        window._current_anim = "idle"  # 8fps
        window._frame_index = 0
        window._frame_timer = 0.0
        # At 8fps, interval is 0.125s
        window._animate(0.13)
        assert window._frame_index == 1

    def test_animate_loops(self, window):
        window._current_anim = "idle"
        window._frame_index = 5  # last frame (6 frames)
        window._frame_timer = 0.0
        window._animate(0.13)
        assert window._frame_index == 0

    def test_animate_oneshot_returns(self, window):
        window._current_anim = "waving"
        window._pending_anim = "running"
        window._frame_index = 3  # last frame (4 frames)
        window._frame_timer = 0.0
        window._animate(0.13)
        assert window._current_anim == "running"
        assert window._pending_anim is None


class TestPlayOnce:
    def test_sets_pending(self, window):
        window.timer_phase = "WORK"
        window._play_once("waving")
        assert window._current_anim == "waving"
        assert window._pending_anim == "running"

    def test_blocked_if_pending(self, window):
        window._pending_anim = "idle"
        window._current_anim = "waving"
        window._play_once("jumping")
        assert window._current_anim == "waving"
        assert window._pending_anim == "idle"


class TestTriggerPriority:
    def test_failed_highest(self, window):
        window.sessions = 1
        window._timer_getter = lambda: ("00:00", "WORK", 2, "Done!", 0.0, False)
        window._tick()
        assert window._current_anim == "failed"

    def test_waving_over_jumping(self, window):
        window.sessions = 1
        window.timer_phase = "WORK"
        window._last_phase = "WORK"
        window._timer_getter = lambda: ("05:00", "BREAK", 2, "Break!", 1.0, False)
        window._tick()
        assert window._current_anim == "waving"

    def test_jumping_on_phase_only(self, window):
        window.sessions = 1
        window.timer_phase = "WORK"
        window._last_phase = "WORK"
        window._timer_getter = lambda: ("05:00", "BREAK", 1, "Break!", 1.0, False)
        window._tick()
        assert window._current_anim == "jumping"

    def test_no_trigger_first_tick(self, window):
        window.sessions = 0
        window._last_phase = None
        window._timer_getter = lambda: ("25:00", "WORK", 0, "Focus!", 1.0, False)
        window._tick()
        assert window._current_anim == "running"
        assert window._pending_anim is None


class TestIdleWaiting:
    def test_waiting_after_30s(self, window):
        window._current_anim = "idle"
        window._idle_timer = 30.0
        window._timer_getter = lambda: ("25:00", "BREAK", 0, "Rest!", 1.0, False)
        window._tick()
        assert window._current_anim == "waiting"


class TestReviewAlternation:
    def test_toggle(self, window):
        window._current_anim = "running"
        window._review_toggle = 0
        window._review_toggle_timer = 10.0
        window._last_phase = "WORK"
        window._timer_getter = lambda: ("25:00", "WORK", 0, "Focus!", 0.5, False)
        window._tick()
        assert window._review_toggle == 1
        assert window._current_anim == "review"


class TestDragging:
    def test_drag_right(self, window):
        window._current_anim = "idle"
        window.mousePressEvent(_press(50, 50))
        window.mouseMoveEvent(_move(100, 50))
        assert window._current_anim == "run_right"

    def test_drag_left(self, window):
        window._current_anim = "idle"
        window.mousePressEvent(_press(100, 50))
        window.mouseMoveEvent(_move(50, 50))
        assert window._current_anim == "run_left"

    def test_release_returns(self, window):
        window._current_anim = "run_right"
        window.timer_phase = "WORK"
        window._drag_pos = QPoint(0, 0)
        window._drag_start_pos = QPoint(50, 50)
        window.mouseReleaseEvent(_release(50, 50))
        assert window._current_anim == "running"


class TestClickPause:
    def test_click_toggles(self, window):
        called = []
        window._on_toggle_pause = lambda: called.append(True)
        window.mousePressEvent(_press(50, 50))
        window.mouseReleaseEvent(_release(50, 50))
        assert called == [True]

    def test_drag_no_toggle(self, window):
        called = []
        window._on_toggle_pause = lambda: called.append(True)
        window.mousePressEvent(_press(50, 50))
        window.mouseMoveEvent(_move(150, 50))
        window.mouseReleaseEvent(_release(150, 50))
        assert called == []


class TestDoubleClickReset:
    def test_resets(self, window):
        called = []
        window._on_reset = lambda: called.append(True)
        window.mouseDoubleClickEvent(_dblclick(50, 50))
        assert called == [True]


class TestStatusDisplay:
    def test_progress_clamped(self, window):
        window.set_timer_progress(1.5)
        assert window.timer_progress == 1.0

    def test_sessions(self, window):
        window.set_sessions(5)
        assert window.sessions == 5


class TestRun:
    def test_sets_callbacks(self, window):
        g = lambda: ("10:00", "WORK", 0, "hi", 0.5, False)
        window.run(timer_getter=g, on_toggle_pause=lambda: None, on_reset=lambda: None)
        assert window._timer_getter is g

    def test_tick(self, window):
        window._timer_getter = lambda: ("10:00", "BREAK", 3, "Rest!", 0.25, False)
        window._tick()
        assert window.timer_text == "10:00"
        assert window.paused is False
