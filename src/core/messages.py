"""Pet dialog/message system based on timer phase."""

import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.core.timer import TimerPhase

WORK_MESSAGES = [
    "Focus time! You've got this!",
    "Stay sharp! Great things take effort!",
    "Heads down, power through!",
    "Deep work mode activated!",
    "One pomodoro at a time!",
    "Lock in! Your future self will thank you.",
    "Distractions are temporary. Focus is forever.",
    "You're building something amazing right now.",
]

BREAK_MESSAGES = [
    "Take a break! You earned it!",
    "Rest your eyes, stretch a bit!",
    "Breathe deep, recharge!",
    "Time to stretch those legs!",
    "Relax, you're doing great!",
    "Step away for a moment — you deserve it.",
    "Hydrate! Your brain needs water.",
    "Look at something far away to rest your eyes.",
]

LONG_BREAK_MESSAGES = [
    "Long break! Take a real rest 🌿",
    "You've earned a longer break — go for a walk!",
    "Stretch, hydrate, breathe. You've been crushing it!",
    "Step away from the screen. You deserve this.",
    "Great focus session! Recharge fully.",
    "Go outside for a few minutes. Fresh air helps!",
    "Grab a snack, move around. You've earned it!",
]

# Time-of-day greetings (used as message prefix)
_TIME_GREETINGS = {
    "morning": ["Good morning! ☀️", "Rise and grind! 🌅", "Morning focus! 🌄"],
    "afternoon": ["Afternoon power! 💪", "Keep the momentum! 🔥", "Afternoon push! ⚡"],
    "evening": ["Evening focus! 🌆", "Night owl mode! 🦉", "Late grind! 🌙"],
}

# Custom messages loaded from file (one per line)
_custom_messages: Optional[List[str]] = None


def load_custom_messages(path: str) -> None:
    """Load custom messages from a text file (one per line)."""
    global _custom_messages
    p = Path(path)
    if p.exists():
        lines = [line.strip() for line in p.read_text().splitlines() if line.strip()]
        if lines:
            _custom_messages = lines


def _get_time_of_day() -> str:
    """Return 'morning', 'afternoon', or 'evening' based on current hour."""
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 18:
        return "afternoon"
    else:
        return "evening"


class MessageProvider:
    """Provides messages based on timer phase."""

    @staticmethod
    def get_messages(phase: TimerPhase) -> List[str]:
        if _custom_messages:
            return _custom_messages
        if phase == TimerPhase.WORK:
            return WORK_MESSAGES
        if phase == TimerPhase.LONG_BREAK:
            return LONG_BREAK_MESSAGES
        return BREAK_MESSAGES

    @staticmethod
    def get_message_with_custom(phase: TimerPhase, custom: List[str]) -> str:
        return random.choice(custom)


def get_message(phase: TimerPhase) -> str:
    """Return a random message for the current timer phase.

    For the first work session of a time period, includes a time-of-day greeting.
    """
    messages = MessageProvider.get_messages(phase)
    msg = random.choice(messages)

    # Add time-of-day greeting for work phase (1 in 4 chance)
    if phase == TimerPhase.WORK and random.random() < 0.25:
        tod = _get_time_of_day()
        greeting = random.choice(_TIME_GREETINGS[tod])
        msg = f"{greeting} {msg}"

    return msg
