"""Desktop notifications using macOS osascript — no extra deps."""

import subprocess
import threading


def _escape_osascript(s: str) -> str:
    """Escape a string for safe embedding in an osascript double-quoted literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def notify(title: str, message: str, sound: bool = True) -> None:
    """Show a native macOS notification.

    Args:
        title: Notification title.
        message: Notification body.
        sound: Play the default notification sound.
    """
    safe_title = _escape_osascript(title)
    safe_message = _escape_osascript(message)
    sound_arg = 'with sound name "Glass"' if sound else ""
    script = f'display notification "{safe_message}" with title "{safe_title}" {sound_arg}'

    def _run():
        try:
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass  # osascript not available (non-macOS) — silent fallback

    threading.Thread(target=_run, daemon=True).start()


def notify_session_complete(sessions: int) -> None:
    """Notify when a pomodoro session completes."""
    notify(
        "Pomodoro Complete! 🎉",
        f"Session #{sessions} done. Time for a break!",
    )


def notify_break_over() -> None:
    """Notify when break time is over."""
    notify(
        "Break Over! 💪",
        "Time to focus again!",
    )


def notify_timer_paused() -> None:
    """Notify when timer is paused."""
    notify(
        "Timer Paused ⏸",
        "Click the pet to resume.",
        sound=False,
    )


def notify_long_break() -> None:
    """Notify when a long break starts."""
    notify(
        "Long Break! 🌿",
        "Great work! Take a well-deserved rest.",
    )
