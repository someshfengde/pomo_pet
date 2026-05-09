"""Pet dialog/message system based on timer phase."""

import random
from typing import List

from src.timer import TimerPhase

WORK_MESSAGES = [
    "Focus time! You've got this! 💪",
    "Stay sharp! Great things take effort!",
    "Heads down, power through! 🎯",
    "Deep work mode activated!",
    "One pomodoro at a time!",
]

BREAK_MESSAGES = [
    "Take a break! You earned it! 🌴",
    "Rest your eyes, stretch a bit!",
    "Breathe deep, recharge! ☕",
    "Time to stretch those legs!",
    "Relax, you're doing great! ✨",
]


class MessageProvider:
    """Provides messages based on timer phase."""

    @staticmethod
    def get_messages(phase: TimerPhase) -> List[str]:
        """Return the message list for a given phase."""
        if phase == TimerPhase.WORK:
            return WORK_MESSAGES
        return BREAK_MESSAGES

    @staticmethod
    def get_message_with_custom(phase: TimerPhase, custom: List[str]) -> str:
        """Return a random message from a custom list."""
        return random.choice(custom)


def get_message(phase: TimerPhase) -> str:
    """Return a random message for the current timer phase."""
    messages = MessageProvider.get_messages(phase)
    return random.choice(messages)
