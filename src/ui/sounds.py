"""Sound effects using macOS afplay — no extra deps needed."""

import subprocess
import threading
from pathlib import Path


_SOUNDS_DIR = Path(__file__).parent.parent.parent / "assets" / "sounds"

# Volume: 0 (mute) to 100 (max). afplay -v uses 0.0-1.0+ scale.
_volume: int = 80


def set_volume(vol: int) -> None:
    """Set playback volume (0-100)."""
    global _volume
    _volume = max(0, min(100, vol))


def get_volume() -> int:
    return _volume


def _play_file(path: Path) -> None:
    """Play a sound file in a background thread.

    Gracefully handles missing files and missing afplay (non-macOS).
    """
    if not path.exists() or _volume <= 0:
        return
    vol_scale = _volume / 100.0

    def _run():
        try:
            subprocess.run(
                ["afplay", "-v", str(vol_scale), str(path)],
                capture_output=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass  # afplay not available or sound failed — silent fallback

    threading.Thread(target=_run, daemon=True).start()


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
