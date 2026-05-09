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
        assert "Pomo Pet" in result.output or "pomo" in result.output.lower()

    def test_no_args_shows_help(self, runner):
        result = runner.invoke(cli, [])
        assert result.exit_code in (0, 1, 2)


class TestListPets:
    def test_list_pets_flag(self, runner):
        result = runner.invoke(cli, ["--list-pets"])
        assert result.exit_code == 0
        assert "avocado" in result.output.lower() or "Avocado" in result.output

    def test_list_pets_empty(self, runner, tmp_path):
        with patch("src.cli.get_pets_dir", return_value=tmp_path):
            result = runner.invoke(cli, ["--list-pets"])
            assert result.exit_code == 0
            assert "No pets found" in result.output


class TestCLIOptions:
    def test_pet_option_not_found(self, runner):
        result = runner.invoke(cli, ["--pet", "nonexistent"])
        assert result.exit_code == 1

    def test_work_duration_option(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "--work" in result.output

    def test_break_duration_option(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "--break" in result.output

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_pet_starts_window(self, mock_window_cls, mock_qapp, runner):
        mock_instance = MagicMock()
        mock_window_cls.return_value = mock_instance

        result = runner.invoke(cli, ["--pet", "avocado"])
        assert result.exit_code == 0
        assert "Starting Pomo Pet" in result.output
        mock_instance.run.assert_called_once()

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_custom_durations(self, mock_window_cls, mock_qapp, runner):
        mock_instance = MagicMock()
        mock_window_cls.return_value = mock_instance

        result = runner.invoke(cli, ["--pet", "avocado", "--work", "30", "--break", "10"])
        assert result.exit_code == 0
        assert "30min" in result.output
        assert "10min" in result.output

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_default_durations(self, mock_window_cls, mock_qapp, runner):
        mock_instance = MagicMock()
        mock_window_cls.return_value = mock_instance

        result = runner.invoke(cli, ["--pet", "avocado"])
        assert result.exit_code == 0
        assert "25min" in result.output
        assert "5min" in result.output


class TestTimerGetter:
    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_timer_getter_called_by_window(self, mock_window_cls, mock_qapp, runner):
        mock_instance = MagicMock()
        mock_window_cls.return_value = mock_instance

        runner.invoke(cli, ["--pet", "avocado"])

        _, kwargs = mock_instance.run.call_args
        assert "timer_getter" in kwargs
        assert callable(kwargs["timer_getter"])

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_timer_getter_returns_tuple(self, mock_window_cls, mock_qapp, runner):
        mock_instance = MagicMock()
        mock_window_cls.return_value = mock_instance

        runner.invoke(cli, ["--pet", "avocado"])

        _, kwargs = mock_instance.run.call_args
        getter = kwargs["timer_getter"]
        result = getter()
        assert len(result) == 4
        remaining, phase, sessions, message = result
        assert isinstance(remaining, str)
        assert ":" in remaining
        assert phase in ("WORK", "BREAK")
        assert isinstance(sessions, int)
        assert isinstance(message, str)
        assert len(message) > 0

    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_timer_getter_ticks_on_subsequent_calls(self, mock_window_cls, mock_qapp, runner):
        mock_instance = MagicMock()
        mock_window_cls.return_value = mock_instance

        runner.invoke(cli, ["--pet", "avocado"])

        _, kwargs = mock_instance.run.call_args
        getter = kwargs["timer_getter"]

        import time
        first = getter()
        time.sleep(1.1)
        second = getter()

        def parse_time(s):
            m, sec = s.split(":")
            return int(m) * 60 + int(sec)

        assert parse_time(second[0]) <= parse_time(first[0])
