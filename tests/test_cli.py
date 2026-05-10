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
        assert result.exit_code == 1


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

    def test_help_shows_options(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "--stats" in result.output
        assert "--no-sound" in result.output
        assert "--width" in result.output

    def test_stats_flag(self, runner):
        with patch("src.cli.StatsStore") as mock_store:
            mock_store.return_value.stats = MagicMock(
                total_sessions=5, total_hours=2.5, total_focus_minutes=150,
                total_break_minutes=25, current_streak=3, best_streak=5,
                daily_sessions=2,
            )
            result = runner.invoke(cli, ["--stats"])
            assert result.exit_code == 0
            assert "Total sessions" in result.output
