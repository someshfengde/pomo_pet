"""Tests for the Pomodoro timer logic."""

import pytest
from src.timer import PomodoroTimer, TimerPhase


class TestTimerInit:
    """Test timer initialization."""

    def test_default_durations(self):
        """Timer initializes with 25min work and 5min break by default."""
        timer = PomodoroTimer()
        assert timer.work_duration == 25 * 60
        assert timer.break_duration == 5 * 60

    def test_custom_durations(self):
        """Timer accepts custom work and break durations in minutes."""
        timer = PomodoroTimer(work_minutes=30, break_minutes=10)
        assert timer.work_duration == 30 * 60
        assert timer.break_duration == 10 * 60

    def test_initial_phase_is_work(self):
        """Timer starts in WORK phase."""
        timer = PomodoroTimer()
        assert timer.phase == TimerPhase.WORK

    def test_initial_remaining_equals_work_duration(self):
        """Remaining time starts at full work duration."""
        timer = PomodoroTimer()
        assert timer.remaining == 25 * 60

    def test_initial_session_count_is_zero(self):
        """No sessions completed at start."""
        timer = PomodoroTimer()
        assert timer.sessions_completed == 0


class TestTimerTick:
    """Test timer countdown behavior."""

    def test_tick_decrements_remaining(self):
        """Each tick reduces remaining by 1 second."""
        timer = PomodoroTimer(work_minutes=1)
        timer.tick()
        assert timer.remaining == 60 - 1

    def test_tick_never_goes_negative(self):
        """Timer doesn't go negative - transitions phase instead."""
        timer = PomodoroTimer(work_minutes=1, break_minutes=1)
        # Tick well past work phase
        for _ in range(100):
            timer.tick()
        assert timer.remaining >= 0

    def test_work_phase_transitions_to_break(self):
        """When work timer hits 0, phase switches to BREAK."""
        timer = PomodoroTimer(work_minutes=1, break_minutes=5)
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.BREAK
        assert timer.remaining == 5 * 60

    def test_break_phase_transitions_to_work(self):
        """When break timer hits 0, phase switches back to WORK."""
        timer = PomodoroTimer(work_minutes=1, break_minutes=1)
        # Exhaust work phase
        for _ in range(60):
            timer.tick()
        # Exhaust break phase
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.WORK
        assert timer.remaining == 60

    def test_session_count_increments_on_work_completion(self):
        """Sessions completed increments when a work phase ends."""
        timer = PomodoroTimer(work_minutes=1, break_minutes=1)
        for _ in range(60):
            timer.tick()
        assert timer.sessions_completed == 1

    def test_multiple_sessions(self):
        """Multiple work-break cycles increment session count correctly."""
        timer = PomodoroTimer(work_minutes=1, break_minutes=1)
        # First cycle
        for _ in range(60):
            timer.tick()
        for _ in range(60):
            timer.tick()
        # Second work phase
        for _ in range(60):
            timer.tick()
        assert timer.sessions_completed == 2


class TestTimerFormatting:
    """Test timer display formatting."""

    def test_format_remaining(self):
        """Remaining time formats as MM:SS."""
        timer = PomodoroTimer(work_minutes=25)
        assert timer.format_remaining() == "25:00"

    def test_format_after_tick(self):
        """Format updates after ticking."""
        timer = PomodoroTimer(work_minutes=25)
        timer.tick()
        assert timer.format_remaining() == "24:59"

    def test_format_zero(self):
        """Zero remaining formats as 00:00."""
        timer = PomodoroTimer(work_minutes=1)
        for _ in range(60):
            timer.tick()
        # Now in break phase, but let's test the format on a fresh timer
        timer2 = PomodoroTimer(work_minutes=0)
        # work_duration = 0 means remaining = 0
        assert timer2.format_remaining() == "00:00"
