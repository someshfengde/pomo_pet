"""Integration tests for the full Pomo Pet workflow."""

import json
import pytest
import time
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
    def test_list_pets_shows_avocado(self, runner):
        result = runner.invoke(cli, ["--list-pets"])
        assert result.exit_code == 0
        assert "avocado" in result.output.lower()

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_start_with_avocado(self, mock_window_cls, mock_qapp, runner):
        mock_instance = MagicMock()
        mock_window_cls.return_value = mock_instance

        result = runner.invoke(cli, ["--pet", "avocado"])
        assert result.exit_code == 0
        assert "Avocado" in result.output
        mock_instance.run.assert_called_once()

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_start_with_custom_durations(self, mock_window_cls, mock_qapp, runner):
        mock_instance = MagicMock()
        mock_window_cls.return_value = mock_instance

        result = runner.invoke(cli, ["--pet", "avocado", "--work", "30", "--break", "10"])
        assert result.exit_code == 0
        assert "30min" in result.output
        assert "10min" in result.output

    def test_invalid_pet_name_fails(self, runner):
        result = runner.invoke(cli, ["--pet", "dragon"])
        assert result.exit_code == 1

    def test_no_pet_name_fails(self, runner):
        result = runner.invoke(cli, [])
        assert result.exit_code == 1


class TestTimerIntegration:
    def test_one_minute_work_cycle(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=1)
        assert timer.phase == TimerPhase.WORK
        assert timer.format_remaining() == "01:00"

        for _ in range(59):
            timer.tick()
        assert timer.format_remaining() == "00:01"
        assert timer.phase == TimerPhase.WORK

        timer.tick()
        assert timer.phase == TimerPhase.BREAK
        assert timer.format_remaining() == "01:00"
        assert timer.sessions_completed == 1

    def test_message_changes_with_phase(self):
        work_msg = get_message(TimerPhase.WORK)
        break_msg = get_message(TimerPhase.BREAK)
        assert len(work_msg) > 0
        assert len(break_msg) > 0


class TestPetLoaderIntegration:
    def test_load_real_avocado_pet(self):
        from pathlib import Path
        pets_dir = Path(__file__).parent.parent / "pets"
        pet_dir = pets_dir / "avacado"
        if not pet_dir.exists():
            pytest.skip("avacado pet directory not found")

        pet = load_pet(pet_dir)
        assert pet.id == "avocado"
        assert pet.display_name == "Avocado"
        assert pet.kind == "creature"

    def test_list_real_pets(self):
        from pathlib import Path
        pets_dir = Path(__file__).parent.parent / "pets"
        if not pets_dir.exists():
            pytest.skip("pets directory not found")

        pets = list_pets(pets_dir)
        assert len(pets) >= 1
        ids = [p.id for p in pets]
        assert "avocado" in ids


class TestTimerGetterIntegration:
    def test_timer_getter_returns_correct_format(self):
        timer = PomodoroTimer(work_minutes=25, break_minutes=5)
        current_message = get_message(timer.phase)
        last_phase = timer.phase
        last_tick = time.time()

        def timer_getter():
            nonlocal current_message, last_phase, last_tick
            now = time.time()
            elapsed = now - last_tick
            if elapsed >= 1.0:
                ticks = int(elapsed)
                last_tick += ticks
                for _ in range(ticks):
                    timer.tick()
                if timer.phase != last_phase:
                    current_message = get_message(timer.phase)
                    last_phase = timer.phase
            return (
                timer.format_remaining(),
                timer.phase.value.upper(),
                timer.sessions_completed,
                current_message,
            )

        result = timer_getter()
        assert len(result) == 4
        remaining, phase, sessions, message = result
        assert isinstance(remaining, str)
        assert ":" in remaining
        assert phase in ("WORK", "BREAK")
        assert isinstance(sessions, int)
        assert isinstance(message, str)
