"""CLI entry point for Pomo Pet."""

import json
import sys
import time
from pathlib import Path

import click
from PySide6.QtWidgets import QApplication

from src.pet_loader import list_pets
from src.timer import PomodoroTimer, TimerPhase
from src.messages import get_message
from src.pet_window import PetWindow


def get_pets_dir() -> Path:
    """Return the path to the pets directory."""
    return Path(__file__).parent.parent / "pets"


def _resolve_spritesheet(pet, pets_dir: Path) -> None:
    """Resolve the pet's spritesheet path to an absolute path."""
    for entry in pets_dir.iterdir():
        if entry.is_dir() and (entry / "pet.json").exists():
            try:
                data = json.loads((entry / "pet.json").read_text())
                if data.get("id") == pet.id:
                    pet.spritesheet_path = str(entry / pet.spritesheet_path)
                    return
            except Exception:
                continue


@click.command()
@click.option("--pet", "pet_name", default=None, help="Pet to display (e.g., avocado)")
@click.option("--work", "work_minutes", default=25, type=int, help="Work session duration in minutes (default: 25)")
@click.option("--break", "break_minutes", default=5, type=int, help="Break session duration in minutes (default: 5)")
@click.option("--list-pets", "list_pets_flag", is_flag=True, default=False, help="List all available pets")
def cli(pet_name: str | None, work_minutes: int, break_minutes: int, list_pets_flag: bool) -> None:
    """Pomo Pet - A Pomodoro timer with cute digital pets!"""
    if list_pets_flag:
        pets = list_pets(get_pets_dir())
        if not pets:
            click.echo("No pets found.")
            return
        click.echo("Available pets:")
        for p in pets:
            click.echo(f"  {p.id:12s} - {p.display_name}: {p.description}")
        return

    if pet_name is None:
        click.echo("Please specify a pet with --pet <name>")
        click.echo("Use --list-pets to see available pets.")
        sys.exit(1)

    # Load the selected pet
    pets = list_pets(get_pets_dir())
    pet = next((p for p in pets if p.id == pet_name), None)
    if pet is None:
        click.echo(f"Error: Pet '{pet_name}' not found. Use --list-pets to see available pets.", err=True)
        sys.exit(1)

    _resolve_spritesheet(pet, get_pets_dir())

    click.echo(f"Starting Pomo Pet with {pet.display_name}!")
    click.echo(f"Work: {work_minutes}min | Break: {break_minutes}min")
    click.echo("Press Q or ESC to quit. Drag the pet to move it.")

    # Create timer
    timer = PomodoroTimer(work_minutes=work_minutes, break_minutes=break_minutes)
    current_message = get_message(timer.phase)
    last_phase = timer.phase
    last_tick = time.time()

    def timer_getter():
        nonlocal current_message, last_phase, last_tick

        now = time.time()
        elapsed = now - last_tick
        if elapsed >= 1.0 and not timer.paused:
            ticks = int(elapsed)
            last_tick += ticks
            for _ in range(ticks):
                timer.tick()

            if timer.phase != last_phase:
                current_message = get_message(timer.phase)
                last_phase = timer.phase

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

    def on_reset():
        nonlocal current_message, last_phase
        timer.reset()
        current_message = get_message(timer.phase)
        last_phase = timer.phase

    # Launch the Qt window
    app = QApplication(sys.argv)
    window = PetWindow(pet=pet)
    window.run(timer_getter=timer_getter, on_toggle_pause=on_toggle_pause, on_reset=on_reset)
    app.exec()
