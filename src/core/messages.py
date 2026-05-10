"""Pet dialog/message system based on timer phase."""

import random
from pathlib import Path
from typing import List, Optional

from src.core.timer import TimerPhase

WORK_MESSAGES = [
    "Focus time! You've got this!",
    "Stay sharp! Great things take effort!",
    "Heads down, power through!",
    "Deep work mode activated!",
    "One pomodoro at a time!",
]

BREAK_MESSAGES = [
    "Take a break! You earned it!",
    "Rest your eyes, stretch a bit!",
    "Breathe deep, recharge!",
    "Time to stretch those legs!",
    "Relax, you're doing great!",
]

# Custom messages loaded from file (one per line)
_custom_messages: Optional[List[str]] = None


def load_custom_messages(path: str) -> None:
    """Load custom messages from a text file (one per line)."""
    global _custom_messages
    p = Path(path)
    if p.exists():
        lines = [l.strip() for l in p.read_text().splitlines() if l.strip()]
        if lines:
            _custom_messages = lines


class MessageProvider:
    """Provides messages based on timer phase."""

    @staticmethod
    def get_messages(phase: TimerPhase) -> List[str]:
        if _custom_messages:
            return _custom_messages
        if phase == TimerPhase.WORK:
            return WORK_MESSAGES
        return BREAK_MESSAGES

    @staticmethod
    def get_message_with_custom(phase: TimerPhase, custom: List[str]) -> str:
        return random.choice(custom)


def get_message(phase: TimerPhase) -> str:
    """Return a random message for the current timer phase."""
    messages = MessageProvider.get_messages(phase)
    return random.choice(messages)
