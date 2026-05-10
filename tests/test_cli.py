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

    def test_no_args_shows_help(self, runner):
        result = runner.invoke(cli, [])
        assert "Pomo Pet" in result.output

    def test_start_help(self, runner):
        result = runner.invoke(cli, ["start", "--help"])
        assert result.exit_code == 0


class TestListCommand:
    def test_list_pets(self, runner):
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "avocado" in result.output.lower()

    def test_empty(self, runner, tmp_path):
        with patch("src.cli.get_pets_dir", return_value=tmp_path):
            result = runner.invoke(cli, ["list"])
            assert "No pets found" in result.output


class TestStartCommand:
    def test_unknown_pet(self, runner):
        assert runner.invoke(cli, ["start", "nope"]).exit_code == 1

    def test_default_pet(self, runner):
        """start without argument defaults to avocado."""
        with patch("src.cli.QApplication") as mock_q, \
             patch("src.cli.PetWindow") as mock_w, \
             patch("src.cli.os.fork", return_value=12345):
            mock_w.return_value = MagicMock()
            result = runner.invoke(cli, ["start"])
            assert result.exit_code == 0
            assert "Avocado" in result.output
            assert "12345" in result.output

    @patch("src.cli.os.fork", return_value=12345)
    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_specific_pet(self, mock_w, mock_q, mock_fork, runner):
        mock_w.return_value = MagicMock()
        result = runner.invoke(cli, ["start", "avocado"])
        assert result.exit_code == 0
        assert "Avocado" in result.output

    @patch("src.cli.os.fork", return_value=12345)
    @patch("src.cli.QApplication")
    @patch("src.cli.PetWindow")
    def test_custom_durations(self, mock_w, mock_q, mock_fork, runner):
        mock_w.return_value = MagicMock()
        result = runner.invoke(cli, ["--work", "30", "--break", "10", "start"])
        assert result.exit_code == 0


class TestStatsCommand:
    def test_stats(self, runner):
        with patch("src.cli.StatsStore") as mock_store:
            mock_store.return_value.stats = MagicMock(
                total_sessions=5, total_hours=2.5, total_focus_minutes=150,
                current_streak=3, best_streak=5, daily_sessions=2,
            )
            result = runner.invoke(cli, ["stats"])
            assert result.exit_code == 0
            assert "Sessions" in result.output
