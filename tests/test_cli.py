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
        with patch("src.cli.subprocess") as mock_sub:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_sub.Popen.return_value = mock_proc
            result = runner.invoke(cli, ["start"])
            assert result.exit_code == 0
            assert "Avocado" in result.output
            assert "12345" in result.output

    @patch("src.cli.subprocess")
    def test_specific_pet(self, mock_sub, runner):
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_sub.Popen.return_value = mock_proc
        result = runner.invoke(cli, ["start", "avocado"])
        assert result.exit_code == 0
        assert "Avocado" in result.output

    @patch("src.cli.subprocess")
    def test_custom_durations(self, mock_sub, runner):
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_sub.Popen.return_value = mock_proc
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


class TestConfigCommand:
    def test_config_shows_all_fields(self, runner):
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "default_pet" in result.output
        assert "work_minutes" in result.output
        assert "break_minutes" in result.output
        assert "long_break_minutes" in result.output
        assert "long_break_interval" in result.output
        assert "volume" in result.output
        assert "sound_enabled" in result.output

    def test_config_shows_file_path(self, runner):
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "config.json" in result.output

    def test_config_get_single_key(self, runner):
        result = runner.invoke(cli, ["config", "work_minutes"])
        assert result.exit_code == 0
        assert "work_minutes" in result.output

    def test_config_set_value(self, runner, tmp_path):
        with patch("src.core.config.CONFIG_FILE", tmp_path / "config.json"):
            with patch("src.core.config.CONFIG_DIR", tmp_path):
                result = runner.invoke(cli, ["config", "work_minutes", "30"])
                assert result.exit_code == 0
                assert "work_minutes = 30" in result.output

    def test_config_unknown_key(self, runner):
        result = runner.invoke(cli, ["config", "nonexistent"])
        assert result.exit_code == 1
        assert "Unknown key" in result.output
