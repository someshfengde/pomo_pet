"""Sound effects using macOS afplay — no extra deps needed."""

import subprocess
import threading
from pathlib import Path


_SOUNDS_DIR = Path(__file__).parent.parent.parent / "assets" / "sounds"


def _play_file(path: Path) -> None:
    """Play a sound file in a background thread."""
    if path.exists():
        threading.Thread(
            target=subprocess.run,
            args=(["afplay", str(path)],),
            kwargs={"capture_output": True},
            daemon=True,
        ).start()


def play_tick() -> None:
    """Subtle tick sound (every second — very quiet)."""
    _play_file(_SOUNDS_DIR / "tick.wav")


def play_phase_change() -> None:
    """Gentle chime when phase changes (work -> break or vice versa)."""
    _play_file(_SOUNDS_DIR / "phase_change.wav")


def play_session_complete() -> None:
    """Celebratory sound when a pomodoro session completes."""
    _play_file(_SOUNDS_DIR / "session_complete.wav")


def play_timer_expire() -> None:
    """Alert sound when timer hits zero."""
    _play_file(_SOUNDS_DIR / "timer_expire.wav")


def play_click() -> None:
    """Soft click for pause/resume."""
    _play_file(_SOUNDS_DIR / "click.wav")
