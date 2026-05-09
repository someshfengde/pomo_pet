"""Tests for CLI argument parsing and commands."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from src.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIHelp:
    def test_help_flag(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_no_args(self, runner):
        result = runner.invoke(cli, [])
        assert result.exit_code in (0, 1, 2)


class TestListPets:
    def test_list_pets(self, runner):
        result = runner.invoke(cli, ["--list-pets"])
        assert result.exit_code == 0
        assert "avocado" in result.output.lower()

    def test_empty(self, runner, tmp_path):
        with patch("src.cli.get_pets_dir", return_value=tmp_path):
            result = runner.invoke(cli, ["--list-pets"])
            assert "No pets found" in result.output


class TestCLIOptions:
    def test_unknown_pet(self, runner):
        assert runner.invoke(cli, ["--pet", "nope"]).exit_code == 1

    def test_help_shows_new_options(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "--stats" in result.output
        assert "--no-sound" in result.output

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_starts_window(self, mock_w, mock_q, runner):
        mock_w.return_value = MagicMock()
        result = runner.invoke(cli, ["--pet", "avocado"])
        assert result.exit_code == 0
        assert "Starting Pomo Pet" in result.output

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_custom_durations(self, mock_w, mock_q, runner):
        mock_w.return_value = MagicMock()
        result = runner.invoke(cli, ["--pet", "avocado", "--work", "30", "--break", "10"])
        assert result.exit_code == 0
        assert "30min" in result.output

    def test_stats_flag(self, runner, tmp_path):
        with patch("src.cli.StatsStore") as mock_store:
            mock_store.return_value.stats = MagicMock(
                total_sessions=5, total_hours=2.5, total_focus_minutes=150,
                total_break_minutes=25, current_streak=3, best_streak=5,
                daily_sessions=2,
            )
            result = runner.invoke(cli, ["--stats"])
            assert result.exit_code == 0
            assert "Total sessions" in result.output

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_no_sound_flag(self, mock_w, mock_q, runner):
        mock_w.return_value = MagicMock()
        result = runner.invoke(cli, ["--pet", "avocado", "--no-sound"])
        assert result.exit_code == 0


class TestTimerGetter:
    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_returns_6_values(self, mock_w, mock_q, runner):
        mock_w.return_value = MagicMock()
        runner.invoke(cli, ["--pet", "avocado"])
        getter = mock_w.return_value.run.call_args[1]["timer_getter"]
        result = getter()
        assert len(result) == 6
        remaining, phase, sessions, message, progress, paused = result
        assert isinstance(remaining, str)
        assert ":" in remaining
        assert phase in ("WORK", "BREAK")
        assert isinstance(sessions, int)
        assert isinstance(message, str)
        assert isinstance(progress, float)
        assert isinstance(paused, bool)

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_callbacks_passed(self, mock_w, mock_q, runner):
        mock_w.return_value = MagicMock()
        runner.invoke(cli, ["--pet", "avocado"])
        kwargs = mock_w.return_value.run.call_args[1]
        assert "on_toggle_pause" in kwargs
        assert "on_reset" in kwargs
        assert callable(kwargs["on_toggle_pause"])
        assert callable(kwargs["on_reset"])

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_toggle_pause_callback(self, mock_w, mock_q, runner):
        mock_w.return_value = MagicMock()
        runner.invoke(cli, ["--pet", "avocado"])
        kwargs = mock_w.return_value.run.call_args[1]
        getter = kwargs["timer_getter"]
        on_toggle_pause = kwargs["on_toggle_pause"]

        # Initially not paused
        assert getter()[5] is False

        # Toggle pause
        on_toggle_pause()
        assert getter()[5] is True

        # Toggle again
        on_toggle_pause()
        assert getter()[5] is False

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_reset_callback(self, mock_w, mock_q, runner):
        mock_w.return_value = MagicMock()
        runner.invoke(cli, ["--pet", "avocado"])
        kwargs = mock_w.return_value.run.call_args[1]
        getter = kwargs["timer_getter"]
        on_reset = kwargs["on_reset"]

        # Initial state
        initial_remaining = getter()[0]

        # Simulate time passing (mock time)
        import time
        time.sleep(1.1)
        getter()  # triggers a tick

        # Reset
        on_reset()
        result = getter()
        assert result[0] == initial_remaining
        assert result[5] is False  # not paused
