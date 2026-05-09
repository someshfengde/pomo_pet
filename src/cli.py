"""CLI entry point for Pomo Pet."""

import json
import sys
import time
from pathlib import Path

import click
from PySide6.QtWidgets import QApplication

from src.pets.loader import list_pets
from src.core.timer import PomodoroTimer, TimerPhase
from src.core.messages import get_message
from src.core.stats import StatsStore
from src.ui.window import PetWindow
from src.ui.sounds import play_phase_change, play_session_complete, play_timer_expire, play_click
from src.ui.notifications import notify_session_complete, notify_break_over


def get_pets_dir() -> Path:
    """Return the path to the pets directory."""
    return Path(__file__).parent.parent / "pets"


@click.command()
@click.option("--pet", "pet_name", default=None, help="Pet to display (e.g., avocado)")
@click.option("--work", "work_minutes", default=25, type=int, help="Work session duration in minutes (default: 25)")
@click.option("--break", "break_minutes", default=5, type=int, help="Break session duration in minutes (default: 5)")
@click.option("--list-pets", "list_pets_flag", is_flag=True, default=False, help="List all available pets")
@click.option("--stats", "stats_flag", is_flag=True, default=False, help="Show session statistics")
@click.option("--no-sound", is_flag=True, default=False, help="Disable sound effects")
def cli(pet_name, work_minutes, break_minutes, list_pets_flag, stats_flag, no_sound):
    """Pomo Pet - A Pomodoro timer with cute digital pets!"""

    # --stats: show statistics and exit
    if stats_flag:
        store = StatsStore()
        s = store.stats
        click.echo(f"Total sessions:   {s.total_sessions}")
        click.echo(f"Total focus:      {s.total_hours}h ({s.total_focus_minutes}min)")
        click.echo(f"Total break:      {s.total_break_minutes}min")
        click.echo(f"Current streak:   {s.current_streak}")
        click.echo(f"Best streak:      {s.best_streak}")
        click.echo(f"Today:            {s.daily_sessions} sessions")
        return

    # --list-pets: show available pets and exit
    if list_pets_flag:
        pets = list_pets(get_pets_dir())
        if not pets:
            click.echo("No pets found.")
            return
        click.echo("Available pets:")
        for p in pets:
            click.echo(f"  {p.id:12s} - {p.display_name}: {p.description}")
        return

    # --pet required
    if pet_name is None:
        click.echo("Please specify a pet with --pet <name>")
        click.echo("Use --list-pets to see available pets.")
        sys.exit(1)

    # Load pet
    pets = list_pets(get_pets_dir())
    pet = next((p for p in pets if p.id == pet_name), None)
    if pet is None:
        click.echo(f"Error: Pet '{pet_name}' not found. Use --list-pets to see available pets.", err=True)
        sys.exit(1)

    # Stats
    store = StatsStore()

    click.echo(f"Starting Pomo Pet with {pet.display_name}!")
    click.echo(f"Work: {work_minutes}min | Break: {break_minutes}min")
    if store.stats.total_sessions > 0:
        click.echo(f"Stats: {store.summary}")
    click.echo("Press Q or ESC to quit. Drag the pet to move it.")

    # Timer
    timer = PomodoroTimer(work_minutes=work_minutes, break_minutes=break_minutes)
    current_message = get_message(timer.phase)
    last_phase = timer.phase
    last_sessions = timer.sessions_completed
    last_tick = time.time()

    def timer_getter():
        nonlocal current_message, last_phase, last_sessions, last_tick

        now = time.time()
        elapsed = now - last_tick
        if elapsed >= 1.0 and not timer.paused:
            ticks = int(elapsed)
            last_tick += ticks
            for _ in range(ticks):
                timer.tick()

            # Phase change
            if timer.phase != last_phase:
                current_message = get_message(timer.phase)
                if not no_sound:
                    play_phase_change()
                if timer.phase == TimerPhase.WORK:
                    notify_break_over()
                last_phase = timer.phase

            # Session complete
            if timer.sessions_completed > last_sessions:
                store.record_session(work_minutes, break_minutes)
                if not no_sound:
                    play_session_complete()
                notify_session_complete(timer.sessions_completed)
                last_sessions = timer.sessions_completed

        total = timer.work_duration if timer.phase == TimerPhase.WORK else timer.break_duration
        return (
            timer.format_remaining(),
            timer.phase.value.upper(),
            timer.sessions_completed,
            current_message,
            timer.remaining / max(total, 1),
            timer.paused,
        )

    def on_toggle_pause():
        timer.toggle_pause()
        if not no_sound:
            play_click()

    def on_reset():
        nonlocal current_message, last_phase
        timer.reset()
        current_message = get_message(timer.phase)
        last_phase = timer.phase
        if not no_sound:
            play_click()

    # Launch window
    app = QApplication(sys.argv)
    window = PetWindow(pet=pet)
    window.run(timer_getter=timer_getter, on_toggle_pause=on_toggle_pause, on_reset=on_reset)

    # Tray icon
    from src.ui.tray import TrayManager
    tray = TrayManager(
        on_pause=on_toggle_pause,
        on_reset=on_reset,
        on_quit=app.quit,
    )
    tray.show()

    app.exec()
