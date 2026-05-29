"""Session statistics tracking and persistence."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class SessionStats:
    """Tracks pomodoro session statistics."""

    total_sessions: int = 0
    total_focus_minutes: int = 0
    total_break_minutes: int = 0
    current_streak: int = 0
    best_streak: int = 0
    last_session_date: str = ""
    daily_sessions: int = 0
    daily_date: str = ""

    def record_session(self, focus_minutes: int, break_minutes: int) -> None:
        """Record a completed pomodoro session."""
        today = date.today().isoformat()

        # Reset daily count if new day
        if self.daily_date != today:
            self.daily_sessions = 0
            self.daily_date = today

        self.total_sessions += 1
        self.total_focus_minutes += focus_minutes
        self.total_break_minutes += break_minutes
        self.daily_sessions += 1

        # Streak logic: continue if last session was today or yesterday
        if self.last_session_date == today:
            # Same day — keep counting
            self.current_streak += 1
        elif self.last_session_date:
            try:
                last = date.fromisoformat(self.last_session_date)
                if date.today() - last == timedelta(days=1):
                    # Consecutive day — extend streak
                    self.current_streak += 1
                else:
                    # Gap — reset streak
                    self.current_streak = 1
            except ValueError:
                self.current_streak = 1
        else:
            # First ever session
            self.current_streak = 1

        self.best_streak = max(self.best_streak, self.current_streak)
        self.last_session_date = today

    @property
    def total_hours(self) -> float:
        return round(self.total_focus_minutes / 60, 1)

    @property
    def today_label(self) -> str:
        today = date.today().isoformat()
        if self.daily_date == today:
            return f"{self.daily_sessions} today"
        return "0 today"


class StatsStore:
    """Persists stats to a JSON file."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path.home() / ".pomo-pet" / "stats.json"
        self.stats = self._load()

    def _load(self) -> SessionStats:
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text())
                return SessionStats(**data)
        except Exception:
            pass
        return SessionStats()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(self.stats), indent=2))

    def record_session(self, focus_minutes: int, break_minutes: int) -> None:
        self.stats.record_session(focus_minutes, break_minutes)
        self.save()

    @property
    def summary(self) -> str:
        s = self.stats
        return (
            f"{s.total_sessions} sessions · "
            f"{s.total_hours}h focused · "
            f"{s.today_label}"
        )
