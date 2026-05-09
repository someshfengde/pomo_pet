"""Pomodoro timer logic and state management."""

from enum import Enum


class TimerPhase(Enum):
    """Timer phases."""
    WORK = "work"
    BREAK = "break"


class PomodoroTimer:
    """A Pomodoro timer with work/break phases, pause, and reset."""

    def __init__(self, work_minutes: int = 25, break_minutes: int = 5) -> None:
        self.work_minutes: int = work_minutes
        self.break_minutes: int = break_minutes
        self.work_duration: int = work_minutes * 60
        self.break_duration: int = break_minutes * 60
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
        if self.phase == TimerPhase.WORK:
            self.remaining = self.work_duration
        else:
            self.remaining = self.break_duration
        self.paused = False

    def _transition_if_needed(self) -> None:
        """Switch phase when current phase reaches zero."""
        if self.phase == TimerPhase.WORK:
            self.sessions_completed += 1
            self.phase = TimerPhase.BREAK
            self.remaining = self.break_duration
        elif self.phase == TimerPhase.BREAK:
            self.phase = TimerPhase.WORK
            self.remaining = self.work_duration

    def format_remaining(self) -> str:
        """Return remaining time as MM:SS string."""
        minutes = self.remaining // 60
        seconds = self.remaining % 60
        return f"{minutes:02d}:{seconds:02d}"
