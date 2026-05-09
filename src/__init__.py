"""Pomo Pet — Pomodoro timer with animated desktop pets."""

from src.core.timer import PomodoroTimer, TimerPhase
from src.core.messages import get_message, MessageProvider
from src.pets.models import Pet, AnimationDef
from src.pets.loader import load_pet, list_pets, PetLoadError
