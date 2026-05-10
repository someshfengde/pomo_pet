"""Integration tests for the full Pomo Pet workflow."""

import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from src.cli import cli
from src.core.timer import PomodoroTimer, TimerPhase
from src.pets.loader import load_pet, list_pets
from src.core.messages import get_message


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

    def test_no_pet(self, runner):
        assert runner.invoke(cli, []).exit_code == 1


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
