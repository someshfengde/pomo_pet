"""CLI entry point for Pomo Pet."""

import json
import os
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
from src.ui.sounds import play_phase_change, play_session_complete, play_click
from src.ui.notifications import notify_session_complete, notify_break_over


def get_pets_dir() -> Path:
    return Path(__file__).parent.parent / "pets"


def _start_pet(pet_name: str, work_minutes: int, break_minutes: int, no_sound: bool) -> None:
    """Launch a pet with timer."""
    pets = list_pets(get_pets_dir())
    pet = next((p for p in pets if p.id == pet_name), None)
    if pet is None:
        click.echo(f"Pet '{pet_name}' not found. Run 'pomo-pet list' to see available pets.", err=True)
        sys.exit(1)

    store = StatsStore()
    click.echo(f"Starting {pet.display_name} | Work: {work_minutes}min | Break: {break_minutes}min")
    if store.stats.total_sessions > 0:
        click.echo(f"Stats: {store.summary}")
    click.echo("Drag to move · Click to pause · Double-click to reset · Q to quit")

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
            if timer.phase != last_phase:
                current_message = get_message(timer.phase)
                if not no_sound:
                    play_phase_change()
                if timer.phase == TimerPhase.WORK:
                    notify_break_over()
                last_phase = timer.phase
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

    # Fork to background so terminal is freed immediately
    pid = os.fork()
    if pid > 0:
        # Parent: print info and exit
        click.echo(f"{pet.display_name} running in background (PID {pid})")
        click.echo("Drag to move · Click to pause · Double-click to reset")
        return

    # Child: detach from terminal and run the Qt app
    os.setsid()
    # Close stdin so terminal input isn't stolen
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)

    app = QApplication(sys.argv)
    window = PetWindow(pet=pet)
    window.run(timer_getter=timer_getter, on_toggle_pause=on_toggle_pause, on_reset=on_reset)
    app.exec()


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--work", "work_minutes", default=25, type=int, help="Work duration (min)")
@click.option("--break", "break_minutes", default=5, type=int, help="Break duration (min)")
@click.option("--no-sound", is_flag=True, help="Disable sounds")
def cli(ctx, work_minutes, break_minutes, no_sound):
    """Pomo Pet - Pomodoro timer with animated pets."""
    ctx.ensure_object(dict)
    ctx.obj["work"] = work_minutes
    ctx.obj["break"] = break_minutes
    ctx.obj["no_sound"] = no_sound

    if ctx.invoked_subcommand is None:
        # No subcommand → show help
        click.echo(ctx.get_help())


@cli.command()
@click.argument("pet_name", default="avocado")
@click.pass_context
def start(ctx, pet_name):
    """Start a pet. Default: avocado.

    \b
    Examples:
      pomo-pet start              # Launch avocado
      pomo-pet start avocado      # Launch avocado
      pomo-pet start --work 30    # 30min work sessions
    """
    _start_pet(pet_name, ctx.obj["work"], ctx.obj["break"], ctx.obj["no_sound"])


@cli.command("list")
def list_cmd():
    """List available pets."""
    pets = list_pets(get_pets_dir())
    if not pets:
        click.echo("No pets found.")
        return
    click.echo("Available pets:")
    for p in pets:
        click.echo(f"  {p.id:12s} - {p.display_name}: {p.description}")


@cli.command()
def stats():
    """Show session statistics."""
    store = StatsStore()
    s = store.stats
    click.echo(f"Sessions:      {s.total_sessions}")
    click.echo(f"Focus time:    {s.total_hours}h ({s.total_focus_minutes}min)")
    click.echo(f"Streak:        {s.current_streak} (best: {s.best_streak})")
    click.echo(f"Today:         {s.daily_sessions} sessions")
