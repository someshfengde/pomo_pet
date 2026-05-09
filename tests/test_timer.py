"""Tests for the Pomodoro timer logic."""

import pytest
from src.timer import PomodoroTimer, TimerPhase


class TestTimerInit:
    def test_default_durations(self):
        timer = PomodoroTimer()
        assert timer.work_duration == 25 * 60
        assert timer.break_duration == 5 * 60

    def test_custom_durations(self):
        timer = PomodoroTimer(work_minutes=30, break_minutes=10)
        assert timer.work_duration == 30 * 60
        assert timer.break_duration == 10 * 60

    def test_initial_phase_is_work(self):
        timer = PomodoroTimer()
        assert timer.phase == TimerPhase.WORK

    def test_initial_remaining(self):
        timer = PomodoroTimer()
        assert timer.remaining == 25 * 60

    def test_initial_sessions_zero(self):
        timer = PomodoroTimer()
        assert timer.sessions_completed == 0

    def test_initial_not_paused(self):
        timer = PomodoroTimer()
        assert timer.paused is False


class TestTimerTick:
    def test_tick_decrements(self):
        timer = PomodoroTimer(work_minutes=1)
        timer.tick()
        assert timer.remaining == 60 - 1

    def test_tick_never_goes_negative(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=1)
        for _ in range(100):
            timer.tick()
        assert timer.remaining >= 0

    def test_work_to_break_transition(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=5)
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.BREAK
        assert timer.remaining == 5 * 60

    def test_break_to_work_transition(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=1)
        for _ in range(120):
            timer.tick()
        assert timer.phase == TimerPhase.WORK

    def test_session_count_increments(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=1)
        for _ in range(60):
            timer.tick()
        assert timer.sessions_completed == 1


class TestTimerPause:
    def test_tick_noop_when_paused(self):
        timer = PomodoroTimer(work_minutes=1)
        timer.tick()
        assert timer.remaining == 59
        timer.paused = True
        timer.tick()
        assert timer.remaining == 59  # didn't change

    def test_toggle_pause(self):
        timer = PomodoroTimer()
        assert timer.paused is False
        timer.toggle_pause()
        assert timer.paused is True
        timer.toggle_pause()
        assert timer.paused is False

    def test_paused_ticks_dont_count(self):
        timer = PomodoroTimer(work_minutes=1)
        timer.paused = True
        for _ in range(100):
            timer.tick()
        assert timer.remaining == 60  # nothing happened


class TestTimerReset:
    def test_reset_work_phase(self):
        timer = PomodoroTimer(work_minutes=25)
        timer.tick()
        timer.tick()
        assert timer.remaining < 25 * 60
        timer.reset()
        assert timer.remaining == 25 * 60
        assert timer.paused is False

    def test_reset_break_phase(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=5)
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.BREAK
        timer.tick()
        timer.reset()
        assert timer.remaining == 5 * 60
        assert timer.phase == TimerPhase.BREAK

    def test_reset_unpauses(self):
        timer = PomodoroTimer()
        timer.paused = True
        timer.reset()
        assert timer.paused is False


class TestTimerFormatting:
    def test_format(self):
        timer = PomodoroTimer(work_minutes=25)
        assert timer.format_remaining() == "25:00"

    def test_format_after_tick(self):
        timer = PomodoroTimer(work_minutes=25)
        timer.tick()
        assert timer.format_remaining() == "24:59"
