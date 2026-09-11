"""Pomodoro timer logic and state management."""

from enum import Enum


class TimerPhase(Enum):
    """Timer phases."""
    WORK = "work"
    BREAK = "break"
    LONG_BREAK = "long_break"


class PomodoroTimer:
    """A Pomodoro timer with work/break/long-break phases, pause, reset, and skip.

    Args:
        work_minutes: Duration of work sessions in minutes.
        break_minutes: Duration of short breaks in minutes.
        long_break_minutes: Duration of long breaks in minutes.
        long_break_interval: Number of work sessions before a long break (0 to disable).
    """

    def __init__(
        self,
        work_minutes: int = 25,
        break_minutes: int = 5,
        long_break_minutes: int = 15,
        long_break_interval: int = 4,
    ) -> None:
        self.work_minutes: int = work_minutes
        self.break_minutes: int = break_minutes
        self.long_break_minutes: int = long_break_minutes
        self.long_break_interval: int = long_break_interval
        self.work_duration: int = work_minutes * 60
        self.break_duration: int = break_minutes * 60
        self.long_break_duration: int = long_break_minutes * 60
        self.phase: TimerPhase = TimerPhase.WORK
        self.remaining: int = self.work_duration
        self.sessions_completed: int = 0
        self.paused: bool = False

    def tick(self) -> None:
        """Advance the timer by one second. No-op when paused."""
        if self.paused:
            return
        if self.remaining > 0:
            self.remaining -= 1
        if self.remaining == 0:
            self._transition_if_needed()

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        self.paused = not self.paused

    def reset(self) -> None:
        """Reset timer to start of current phase."""
        self.remaining = self._duration_for_phase(self.phase)
        self.paused = False

    def skip_phase(self) -> None:
        """Skip to the next phase immediately."""
        self._transition_if_needed()
        self.paused = False

    def _duration_for_phase(self, phase: TimerPhase) -> int:
        """Return the duration in seconds for a given phase."""
        if phase == TimerPhase.WORK:
            return self.work_duration
        elif phase == TimerPhase.LONG_BREAK:
            return self.long_break_duration
        return self.break_duration

    def _transition_if_needed(self) -> None:
        """Switch phase when current phase reaches zero."""
        if self.phase == TimerPhase.WORK:
            self.sessions_completed += 1
            # Check if it's time for a long break
            if (self.long_break_interval > 0
                    and self.sessions_completed % self.long_break_interval == 0):
                self.phase = TimerPhase.LONG_BREAK
                self.remaining = self.long_break_duration
            else:
                self.phase = TimerPhase.BREAK
                self.remaining = self.break_duration
        else:
            # Both BREAK and LONG_BREAK transition to WORK
            self.phase = TimerPhase.WORK
            self.remaining = self.work_duration

    def format_remaining(self) -> str:
        """Return remaining time as MM:SS string."""
        minutes = self.remaining // 60
        seconds = self.remaining % 60
        return f"{minutes:02d}:{seconds:02d}"
