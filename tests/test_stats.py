"""Tests for session statistics."""

import json
import pytest
from pathlib import Path
from src.core.stats import SessionStats, StatsStore


class TestSessionStats:
    def test_initial_state(self):
        s = SessionStats()
        assert s.total_sessions == 0
        assert s.total_focus_minutes == 0
        assert s.current_streak == 0
        assert s.best_streak == 0

    def test_record_session(self):
        s = SessionStats()
        s.record_session(25, 5)
        assert s.total_sessions == 1
        assert s.total_focus_minutes == 25
        assert s.total_break_minutes == 5
        assert s.current_streak == 1

    def test_multiple_sessions_same_day(self):
        s = SessionStats()
        s.record_session(25, 5)
        s.record_session(25, 5)
        assert s.total_sessions == 2
        assert s.current_streak == 2
        assert s.best_streak == 2
        assert s.daily_sessions == 2

    def test_total_hours(self):
        s = SessionStats()
        s.total_focus_minutes = 150
        assert s.total_hours == 2.5

    def test_today_label(self):
        s = SessionStats()
        s.record_session(25, 5)
        assert "1 today" in s.today_label


class TestStatsStore:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "stats.json"
        store = StatsStore(path=path)
        store.record_session(25, 5)

        store2 = StatsStore(path=path)
        assert store2.stats.total_sessions == 1
        assert store2.stats.total_focus_minutes == 25

    def test_corrupted_file_returns_default(self, tmp_path):
        path = tmp_path / "stats.json"
        path.write_text("not json")
        store = StatsStore(path=path)
        assert store.stats.total_sessions == 0

    def test_summary(self, tmp_path):
        path = tmp_path / "stats.json"
        store = StatsStore(path=path)
        store.record_session(25, 5)
        assert "1 sessions" in store.summary
        assert "today" in store.summary
