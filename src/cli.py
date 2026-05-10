"""CLI entry point for Pomo Pet."""

import json
import sys
import time
from pathlib import Path

import click

from src.pets.loader import list_pets
from src.core.timer import PomodoroTimer, TimerPhase
from src.core.messages import get_message
from src.core.stats import StatsStore
from src.ui.ascii_renderer import load_ascii_frames, AsciiAnimator, clear_lines, render_frame
from src.ui.sounds import play_phase_change, play_session_complete, play_click


def get_pets_dir() -> Path:
    return Path(__file__).parent.parent / "pets"


@click.command()
@click.option("--pet", "pet_name", default=None, help="Pet to display (e.g., avocado)")
@click.option("--work", "work_minutes", default=25, type=int, help="Work duration in minutes")
@click.option("--break", "break_minutes", default=5, type=int, help="Break duration in minutes")
@click.option("--list-pets", "list_pets_flag", is_flag=True, help="List available pets")
@click.option("--stats", "stats_flag", is_flag=True, help="Show session statistics")
@click.option("--no-sound", is_flag=True, help="Disable sound effects")
@click.option("--width", "ascii_width", default=0, type=int, help="ASCII art width (0=auto)")
def cli(pet_name, work_minutes, break_minutes, list_pets_flag, stats_flag, no_sound, ascii_width):
    """Pomo Pet - A Pomodoro timer with animated pets!"""

    if stats_flag:
        store = StatsStore()
        s = store.stats
        click.echo(f"Total sessions:   {s.total_sessions}")
        click.echo(f"Total focus:      {s.total_hours}h ({s.total_focus_minutes}min)")
        click.echo(f"Current streak:   {s.current_streak}")
        click.echo(f"Best streak:      {s.best_streak}")
        click.echo(f"Today:            {s.daily_sessions} sessions")
        return

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
        click.echo("Usage: pomo-pet --pet <name>")
        click.echo("       pomo-pet --list-pets")
        sys.exit(1)

    # Load pet
    pets = list_pets(get_pets_dir())
    pet = next((p for p in pets if p.id == pet_name), None)
    if pet is None:
        click.echo(f"Pet '{pet_name}' not found. Use --list-pets.", err=True)
        sys.exit(1)

    # Load ASCII frames for idle animation
    idle_anim = pet.animations.get("idle")
    if idle_anim:
        ascii_frames = load_ascii_frames(
            pet.spritesheet_path,
            pet.frame_width, pet.frame_height,
            row=idle_anim.row,
            num_frames=idle_anim.frames,
            display_width=ascii_width if ascii_width > 0 else None,
        )
        idle_fps = idle_anim.fps
    else:
        ascii_frames = []
        idle_fps = 8

    if not ascii_frames:
        click.echo(f"Could not load spritesheet for {pet.display_name}")
        sys.exit(1)

    animator = AsciiAnimator(ascii_frames, fps=idle_fps, loop=True)

    # Timer
    store = StatsStore()
    timer = PomodoroTimer(work_minutes=work_minutes, break_minutes=break_minutes)
    current_message = get_message(timer.phase)
    last_phase = timer.phase
    last_sessions = timer.sessions_completed
    last_tick = time.time()

    # Hide cursor
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    frame_lines = ascii_frames[0].count("\n") + 1
    first_render = True

    try:
        while True:
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
                    last_phase = timer.phase

                if timer.sessions_completed > last_sessions:
                    store.record_session(work_minutes, break_minutes)
                    if not no_sound:
                        play_session_complete()
                    last_sessions = timer.sessions_completed

            # Build display
            frame = animator.current_frame()
            timer_str = timer.format_remaining()
            phase = timer.phase.value.upper()
            progress_bar = _make_progress_bar(timer)
            pause_str = " [PAUSED]" if timer.paused else ""

            output = (
                f"{frame}\n"
                f"\n"
                f"  {timer_str} {phase}{pause_str}\n"
                f"  {progress_bar}\n"
                f"  {current_message}\n"
                f"  Sessions: {timer.sessions_completed}\n"
            )

            if not first_render:
                clear_lines(frame_lines + 5)
            first_render = False

            render_frame(output)
            time.sleep(1.0 / 30)  # 30fps render loop

    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor
        sys.stdout.write("\033[?25h")
        sys.stdout.write("\n")
        sys.stdout.flush()


def _make_progress_bar(timer: PomodoroTimer, width: int = 30) -> str:
    """Create a text progress bar."""
    total = timer.work_duration if timer.phase == TimerPhase.WORK else timer.break_duration
    progress = 1.0 - (timer.remaining / max(total, 1))
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}]"
