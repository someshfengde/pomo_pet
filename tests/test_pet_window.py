"""Tests for the PySide6 pet display window."""

import sys
import pytest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from src.pet_window import PetWindow, WindowConfig, Theme
from src.pet_loader import AnimationDef, Pet
from PySide6.QtCore import Qt, QPoint


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
            "running": AnimationDef(row=7, frames=6, fps=10, loop=True),
            "failed": AnimationDef(row=5, frames=8, fps=10, loop=False),
        },
    )


@pytest.fixture
def window(test_pet):
    w = PetWindow(pet=test_pet)
    yield w
    w.close()


class TestWindowConfig:
    def test_default(self):
        c = WindowConfig()
        assert c.width == Theme.WIDTH
        assert c.height == Theme.HEIGHT

    def test_custom(self):
        c = WindowConfig(width=300, height=400)
        assert c.width == 300


class TestPetWindowInit:
    def test_stores_pet(self, window):
        assert window.pet.display_name == "TestPet"

    def test_initial_state(self, window):
        assert window._drag_pos is None
        assert window.timer_text == "25:00"
        assert window.timer_phase == "WORK"
        assert window.timer_progress == 0.0
        assert window.sessions == 0
        assert window._current_anim == "idle"

    def test_flags(self, window):
        assert window.windowFlags() & Qt.FramelessWindowHint
        assert window.testAttribute(Qt.WA_TranslucentBackground)


class TestAnimationSystem:
    def test_loaded(self, window):
        assert "idle" in window._animations
        assert "running" in window._animations

    def test_frame_count(self, window):
        assert len(window._animations["idle"]) == 6
        assert len(window._animations["running"]) == 6

    def test_anim_defs(self, window):
        assert window._anim_defs["idle"].frames == 6
        assert window._anim_defs["idle"].fps == 8

    def test_set_animation(self, window):
        window._set_animation("running")
        assert window._current_anim == "running"
        assert window._frame_index == 0

    def test_set_same_noop(self, window):
        window._frame_index = 3
        window._set_animation("idle")
        assert window._frame_index == 3

    def test_pick_work(self, window):
        assert window._pick_animation("WORK") == "running"

    def test_pick_break(self, window):
        assert window._pick_animation("BREAK") == "idle"

    def test_phase_change_switches_anim(self, window):
        window._current_anim = "idle"
        window._last_phase = "BREAK"
        window._timer_getter = lambda: ("25:00", "WORK", 0, "Focus!", 1.0)
        window._tick()
        assert window._current_anim == "running"

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


class TestDragging:
    def test_press_sets_drag(self, window):
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import QPointF
        e = QMouseEvent(QMouseEvent.MouseButtonPress, QPointF(50, 50), QPointF(50, 50),
                        Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        window.mousePressEvent(e)
        assert window._drag_pos is not None

    def test_release_clears_drag(self, window):
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import QPointF
        window._drag_pos = QPoint(10, 10)
        e = QMouseEvent(QMouseEvent.MouseButtonRelease, QPointF(50, 50), QPointF(50, 50),
                        Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        window.mouseReleaseEvent(e)
        assert window._drag_pos is None


class TestStatusDisplay:
    def test_timer_text(self, window):
        window.set_timer_text("10:00", "BREAK")
        assert window.timer_text == "10:00"
        assert window.timer_phase == "BREAK"

    def test_progress(self, window):
        window.set_timer_progress(0.75)
        assert window.timer_progress == 0.75

    def test_progress_clamped(self, window):
        window.set_timer_progress(1.5)
        assert window.timer_progress == 1.0
        window.set_timer_progress(-0.5)
        assert window.timer_progress == 0.0

    def test_message(self, window):
        window.set_message("Rest!")
        assert window.message == "Rest!"

    def test_message_resets_slide(self, window):
        window._message_slide = 1.0
        window.set_message("New")
        assert window._message_slide == 0.0

    def test_sessions(self, window):
        window.set_sessions(5)
        assert window.sessions == 5


class TestLoadFrames:
    def test_missing_file(self):
        pet = Pet(id="x", display_name="X", description="X",
                  spritesheet_path="/nonexistent.webp", kind="creature")
        w = PetWindow(pet=pet)
        assert w._animations == {}
        w.close()


class TestRun:
    def test_sets_getter(self, window):
        g = lambda: ("10:00", "WORK", 0, "hi", 0.5)
        window.run(timer_getter=g)
        assert window._timer_getter is g

    def test_tick_calls_getter(self, window):
        window._timer_getter = lambda: ("10:00", "BREAK", 3, "Rest!", 0.25)
        window._tick()
        assert window.timer_text == "10:00"
        assert window.timer_phase == "BREAK"
        assert window.sessions == 3
        assert window.message == "Rest!"
        assert window.timer_progress == 0.25
