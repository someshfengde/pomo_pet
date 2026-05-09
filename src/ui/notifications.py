"""Desktop notifications using macOS osascript — no extra deps."""

import subprocess
import threading


def notify(title: str, message: str, sound: bool = True) -> None:
    """Show a native macOS notification.

    Args:
        title: Notification title.
        message: Notification body.
        sound: Play the default notification sound.
    """
    sound_arg = "with sound name \"Glass\"" if sound else ""
    script = f'display notification "{message}" with title "{title}" {sound_arg}'
    threading.Thread(
        target=subprocess.run,
        args=(["osascript", "-e", script],),
        kwargs={"capture_output": True},
        daemon=True,
    ).start()


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
