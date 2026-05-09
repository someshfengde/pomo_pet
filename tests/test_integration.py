"""Integration tests for the full Pomo Pet workflow."""

import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from src.cli import cli
from src.timer import PomodoroTimer, TimerPhase
from src.pet_loader import load_pet, list_pets
from src.messages import get_message


@pytest.fixture
def runner():
    return CliRunner()


class TestFullWorkflow:
    def test_list_pets(self, runner):
        result = runner.invoke(cli, ["--list-pets"])
        assert result.exit_code == 0
        assert "avocado" in result.output.lower()

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_start_pet(self, mock_w, mock_q, runner):
        mock_w.return_value = MagicMock()
        result = runner.invoke(cli, ["--pet", "avocado"])
        assert result.exit_code == 0
        assert "Avocado" in result.output

    def test_invalid_pet(self, runner):
        assert runner.invoke(cli, ["--pet", "dragon"]).exit_code == 1


class TestTimerIntegration:
    def test_work_cycle(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=1)
        assert timer.phase == TimerPhase.WORK
        for _ in range(59):
            timer.tick()
        assert timer.phase == TimerPhase.WORK
        timer.tick()
        assert timer.phase == TimerPhase.BREAK
        assert timer.sessions_completed == 1

    def test_pause_blocks_ticks(self):
        timer = PomodoroTimer(work_minutes=1)
        timer.tick()
        assert timer.remaining == 59
        timer.paused = True
        timer.tick()
        assert timer.remaining == 59

    def test_reset_restores(self):
        timer = PomodoroTimer(work_minutes=25)
        timer.tick()
        timer.reset()
        assert timer.remaining == 25 * 60

    def test_progress_calculation(self):
        timer = PomodoroTimer(work_minutes=25, break_minutes=5)
        progress = timer.remaining / timer.work_duration
        assert progress == 1.0
        timer.tick()
        progress = timer.remaining / timer.work_duration
        assert progress < 1.0

    def test_messages_exist(self):
        assert len(get_message(TimerPhase.WORK)) > 0
        assert len(get_message(TimerPhase.BREAK)) > 0


class TestPetLoaderIntegration:
    def test_load_real_pet(self):
        pets_dir = Path(__file__).parent.parent / "pets" / "avacado"
        if not pets_dir.exists():
            pytest.skip("avacado not found")
        pet = load_pet(pets_dir)
        assert pet.id == "avocado"
        assert pet.frame_width == 192
        assert "idle" in pet.animations

    def test_list_real_pets(self):
        pets_dir = Path(__file__).parent.parent / "pets"
        pets = list_pets(pets_dir)
        assert any(p.id == "avocado" for p in pets)


class TestTimerGetterIntegration:
    def test_returns_correct_format(self):
        timer = PomodoroTimer(work_minutes=25, break_minutes=5)
        current_message = get_message(timer.phase)
        last_phase = timer.phase
        last_tick = time.time()

        def timer_getter():
            nonlocal current_message, last_phase, last_tick
            now = time.time()
            elapsed = now - last_tick
            if elapsed >= 1.0 and not timer.paused:
                ticks = int(elapsed)
                last_tick += ticks
                for _ in range(ticks):
                    timer.tick()
                if timer.phase != last_phase:
                    current_message = get_message(timer.phase)
                    last_phase = timer.phase
            total = timer.work_duration if timer.phase == TimerPhase.WORK else timer.break_duration
            return (
                timer.format_remaining(),
                timer.phase.value.upper(),
                timer.sessions_completed,
                current_message,
                timer.remaining / max(total, 1),
                timer.paused,
            )

        result = timer_getter()
        assert len(result) == 6
        remaining, phase, sessions, message, progress, paused = result
        assert isinstance(remaining, str)
        assert phase in ("WORK", "BREAK")
        assert isinstance(progress, float)
        assert isinstance(paused, bool)
