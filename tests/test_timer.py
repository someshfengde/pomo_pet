"""Tests for the Pomodoro timer logic."""

import pytest
from src.core.timer import PomodoroTimer, TimerPhase


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

    def test_long_break_defaults(self):
        timer = PomodoroTimer()
        assert timer.long_break_duration == 15 * 60
        assert timer.long_break_interval == 4


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
        timer = PomodoroTimer(work_minutes=1, break_minutes=5, long_break_interval=0)
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.BREAK
        assert timer.remaining == 5 * 60

    def test_break_to_work_transition(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=1, long_break_interval=0)
        for _ in range(120):
            timer.tick()
        assert timer.phase == TimerPhase.WORK

    def test_session_count_increments(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=1, long_break_interval=0)
        for _ in range(60):
            timer.tick()
        assert timer.sessions_completed == 1


class TestLongBreak:
    def test_long_break_after_interval(self):
        """After long_break_interval sessions, next break is a long break."""
        timer = PomodoroTimer(work_minutes=1, break_minutes=1,
                              long_break_minutes=10, long_break_interval=2)
        # Session 1: work -> break
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.BREAK
        assert timer.sessions_completed == 1

        # Break -> work
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.WORK

        # Session 2: work -> long break (because 2 % 2 == 0)
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.LONG_BREAK
        assert timer.remaining == 10 * 60
        assert timer.sessions_completed == 2

    def test_long_break_disabled(self):
        """long_break_interval=0 disables long breaks."""
        timer = PomodoroTimer(work_minutes=1, break_minutes=1,
                              long_break_interval=0)
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.BREAK  # not LONG_BREAK

    def test_long_break_to_work(self):
        """Long break transitions back to work."""
        timer = PomodoroTimer(work_minutes=1, break_minutes=1,
                              long_break_minutes=5, long_break_interval=1)
        # work -> long break
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.LONG_BREAK
        # long break -> work
        for _ in range(300):
            timer.tick()
        assert timer.phase == TimerPhase.WORK


class TestSkipPhase:
    def test_skip_work_to_break(self):
        timer = PomodoroTimer(work_minutes=25, break_minutes=5,
                              long_break_interval=0)
        assert timer.phase == TimerPhase.WORK
        timer.skip_phase()
        assert timer.phase == TimerPhase.BREAK
        assert timer.remaining == 5 * 60

    def test_skip_break_to_work(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=5,
                              long_break_interval=0)
        timer.skip_phase()  # work -> break
        assert timer.phase == TimerPhase.BREAK
        timer.skip_phase()  # break -> work
        assert timer.phase == TimerPhase.WORK
        assert timer.remaining == 1 * 60
        assert timer.sessions_completed == 1

    def test_skip_unpauses(self):
        timer = PomodoroTimer()
        timer.paused = True
        timer.skip_phase()
        assert timer.paused is False


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
        timer = PomodoroTimer(work_minutes=1, break_minutes=5, long_break_interval=0)
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.BREAK
        timer.tick()
        timer.reset()
        assert timer.remaining == 5 * 60
        assert timer.phase == TimerPhase.BREAK

    def test_reset_long_break_phase(self):
        timer = PomodoroTimer(work_minutes=1, break_minutes=1,
                              long_break_minutes=10, long_break_interval=1)
        for _ in range(60):
            timer.tick()
        assert timer.phase == TimerPhase.LONG_BREAK
        timer.reset()
        assert timer.remaining == 10 * 60
        assert timer.phase == TimerPhase.LONG_BREAK

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
