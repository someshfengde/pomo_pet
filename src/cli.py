"""CLI entry point for Pomo Pet."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import click

_FOREGROUND_ENV = "_POMO_PET_FOREGROUND"

from src.pets.loader import list_pets
from src.core.timer import PomodoroTimer, TimerPhase
from src.core.messages import get_message, load_custom_messages
from src.core.stats import StatsStore
from src.core.config import Config
from src.ui.sounds import play_phase_change, play_session_complete, play_click, set_volume
from src.ui.notifications import notify_session_complete, notify_break_over, notify_long_break


def get_pets_dir() -> Path:
    return Path(__file__).parent.parent / "pets"


def _set_macos_process_name(name: str) -> None:
    """Set the macOS process name so the dock shows our name, not 'python3.13'."""
    try:
        # Override argv[0] — macOS dock reads the binary name from this
        sys.argv[0] = name
        import AppKit
        AppKit.NSProcessInfo.processInfo().setProcessName_(name)
        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
        # Set the app menu title
        app.mainMenu().itemAtIndex_(0).setTitle_(name)
    except Exception:
        pass


def _start_pet(pet_name: str, work_minutes: int, break_minutes: int, no_sound: bool,
               long_break_minutes: int = 15, long_break_interval: int = 4) -> None:
    """Launch a pet with timer."""
    pets = list_pets(get_pets_dir())
    pet = next((p for p in pets if p.id == pet_name), None)
    if pet is None:
        click.echo(f"Pet '{pet_name}' not found. Run 'pomo-pet list' to see available pets.", err=True)
        sys.exit(1)

    # ── Parent process: spawn child and exit BEFORE loading Qt ──
    # PySide6/Qt starts CoreFoundation threads at import time.
    # subprocess.Popen does fork+exec internally; if Qt threads exist
    # in the parent, the forked child crashes with SIGSEGV because
    # CoreFoundation is not fork-safe on macOS.
    if not os.environ.get(_FOREGROUND_ENV):
        env = os.environ.copy()
        env[_FOREGROUND_ENV] = "1"
        # Find the correct Python with PySide6 — may be in a venv managed by uv
        venv = os.environ.get("VIRTUAL_ENV")
        if venv:
            python_bin = os.path.join(venv, "bin", "python")
        else:
            python_bin = sys.executable

        proc = subprocess.Popen(
            [python_bin, "-m", "src", "start", pet_name],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=os.getcwd(),
            env=env,
        )
        click.echo(f"{pet.display_name} running in background (PID {proc.pid})")
        click.echo("Drag to move · Click to pause · Double-click to reset")
        return

    # ── Foreground child process: safe to import Qt now ──
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon, QPixmap
    from src.ui.window import PetWindow

    store = StatsStore()
    click.echo(f"Starting {pet.display_name} | Work: {work_minutes}min | Break: {break_minutes}min")
    if store.stats.total_sessions > 0:
        click.echo(f"Stats: {store.summary}")
    click.echo("Drag to move · Click to pause · Double-click to reset · Q to quit")

    timer = PomodoroTimer(
        work_minutes=work_minutes,
        break_minutes=break_minutes,
        long_break_minutes=long_break_minutes,
        long_break_interval=long_break_interval,
    )
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
                elif timer.phase == TimerPhase.LONG_BREAK:
                    notify_long_break()
                last_phase = timer.phase
            if timer.sessions_completed > last_sessions:
                store.record_session(work_minutes, break_minutes)
                if not no_sound:
                    play_session_complete()
                notify_session_complete(timer.sessions_completed)
                last_sessions = timer.sessions_completed
        if timer.phase == TimerPhase.WORK:
            total = timer.work_duration
        elif timer.phase == TimerPhase.LONG_BREAK:
            total = timer.long_break_duration
        else:
            total = timer.break_duration
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

    def on_skip():
        nonlocal current_message, last_phase
        timer.skip_phase()
        current_message = get_message(timer.phase)
        last_phase = timer.phase
        if not no_sound:
            play_phase_change()

    # macOS: rename process BEFORE Qt reads argv[0]
    _set_macos_process_name("Pomo Pet")

    app = QApplication(sys.argv)
    app.setApplicationName("Pomo Pet")
    app.setApplicationDisplayName("Pomo Pet")

    # Set app icon from the pet's first idle frame
    icon_path = Path(pet.spritesheet_path)
    if icon_path.exists():
        sheet = QPixmap(str(icon_path))
        if not sheet.isNull():
            icon_frame = sheet.copy(0, 0, pet.frame_width, pet.frame_height)
            app.setWindowIcon(QIcon(icon_frame))

    cfg_obj = Config.load()
    window = PetWindow(pet=pet, pomo_config=cfg_obj)

    # System tray integration
    from src.ui.tray import TrayManager
    tray = TrayManager(on_pause=on_toggle_pause, on_reset=on_reset,
                       on_quit=lambda: app.quit())
    tray.show()

    # Update tray tooltip with timer status each tick
    _original_timer_getter = timer_getter
    def timer_getter_with_tray():
        result = _original_timer_getter()
        remaining, phase, sessions, message, progress, paused = result
        tray.update_timer(remaining, phase)
        return result

    window.run(timer_getter=timer_getter_with_tray, on_toggle_pause=on_toggle_pause,
               on_reset=on_reset, on_skip=on_skip)
    app.exec()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(package_name="pomo-pet", prog_name="pomo-pet")
@click.option("--work", "work_minutes", default=None, type=int, help="Work duration (min)")
@click.option("--break", "break_minutes", default=None, type=int, help="Break duration (min)")
@click.option("--volume", default=None, type=int, help="Sound volume (0-100)")
@click.option("--no-sound", is_flag=True, help="Disable sounds")
@click.option("--messages-file", default=None, type=click.Path(exists=True), help="Custom messages file (one per line)")
def cli(ctx, work_minutes, break_minutes, volume, no_sound, messages_file):
    """Pomo Pet - Pomodoro timer with animated pets."""
    ctx.ensure_object(dict)
    cfg = Config.load()
    ctx.obj["config"] = cfg
    ctx.obj["work"] = work_minutes if work_minutes is not None else cfg.work_minutes
    ctx.obj["break"] = break_minutes if break_minutes is not None else cfg.break_minutes
    ctx.obj["no_sound"] = no_sound if no_sound else not cfg.sound_enabled

    # Apply volume from config or CLI flag
    vol = volume if volume is not None else cfg.volume
    set_volume(0 if no_sound else vol)

    # Load custom messages from CLI flag or config
    msg_file = messages_file or cfg.messages_file
    if msg_file:
        load_custom_messages(msg_file)

    # Save overrides to config when user passes them explicitly
    updates = {}
    if work_minutes is not None:
        updates["work_minutes"] = work_minutes
    if break_minutes is not None:
        updates["break_minutes"] = break_minutes
    if volume is not None:
        updates["volume"] = volume
    if no_sound:
        updates["sound_enabled"] = False
    if messages_file is not None:
        updates["messages_file"] = messages_file
    if updates:
        cfg.update(**updates)

    if ctx.invoked_subcommand is None:
        # No subcommand → show help
        click.echo(ctx.get_help())


@cli.command()
@click.argument("pet_name", default=None)
@click.pass_context
def start(ctx, pet_name):
    """Start a pet. Default: from config (avocado).

    \b
    Examples:
      pomo-pet start              # Launch default pet
      pomo-pet start avocado      # Launch avocado
      pomo-pet --work 30 start    # 30min work sessions
    """
    cfg = ctx.obj["config"]
    pet = pet_name or cfg.default_pet
    _start_pet(pet, ctx.obj["work"], ctx.obj["break"], ctx.obj["no_sound"],
               cfg.long_break_minutes, cfg.long_break_interval)


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
@click.option("--format", "fmt", type=click.Choice(["text", "json", "csv"]),
              default="text", help="Output format")
def stats(fmt):
    """Show session statistics.

    \b
    Examples:
      pomo-pet stats                  # Show stats as text
      pomo-pet stats --format json    # Export as JSON
      pomo-pet stats --format csv     # Export as CSV
    """
    store = StatsStore()
    if fmt == "json":
        click.echo(store.export_json())
        return
    if fmt == "csv":
        click.echo(store.export_csv(), nl=False)
        return
    s = store.stats
    click.echo(f"Sessions:      {s.total_sessions}")
    click.echo(f"Focus time:    {s.total_hours}h ({s.total_focus_minutes}min)")
    click.echo(f"Streak:        {s.current_streak} (best: {s.best_streak})")
    click.echo(f"Today:         {s.daily_sessions} sessions")


@cli.command("config")
@click.argument("key", required=False)
@click.argument("value", required=False)
def config_cmd(key, value):
    """View or set config values.

    \b
    Examples:
      pomo-pet config                    # Show all config
      pomo-pet config default_pet cat    # Set default pet
      pomo-pet config work_minutes 30    # Set work duration
      pomo-pet config volume 50          # Set volume (0-100)
    """
    cfg = Config.load()
    if key is None:
        from src.core.config import CONFIG_FILE
        click.echo(f"Config file: {CONFIG_FILE}")
        click.echo(f"  default_pet:         {cfg.default_pet}")
        click.echo(f"  work_minutes:        {cfg.work_minutes}")
        click.echo(f"  break_minutes:       {cfg.break_minutes}")
        click.echo(f"  long_break_minutes:  {cfg.long_break_minutes}")
        click.echo(f"  long_break_interval: {cfg.long_break_interval}")
        click.echo(f"  volume:              {cfg.volume}")
        click.echo(f"  sound_enabled:       {cfg.sound_enabled}")
        click.echo(f"  messages_file:       {cfg.messages_file or '(none)'}")
        return

    if value is None:
        val = getattr(cfg, key, None)
        if val is None:
            click.echo(f"Unknown key: {key}", err=True)
            sys.exit(1)
        click.echo(f"{key} = {val}")
        return

    # Convert value to the right type
    field_types = {f.name: f.type for f in cfg.__dataclass_fields__.values()}
    if key not in field_types:
        click.echo(f"Unknown key: {key}. Valid: {', '.join(field_types)}", err=True)
        sys.exit(1)

    # Cast to correct type
    ft = field_types[key]
    if ft == "int":
        value = int(value)
    elif ft == "bool":
        value = value.lower() in ("true", "1", "yes")
    elif ft == "Optional[str]":
        value = value if value != "none" else None

    cfg.update(**{key: value})
    click.echo(f"Set {key} = {value}")


# Pomodoro technique presets
PRESETS = {
    "classic": {"work": 25, "break": 5, "long_break": 15, "interval": 4,
                "desc": "Classic Pomodoro (25/5, long break every 4)"},
    "52-17": {"work": 52, "break": 17, "long_break": 0, "interval": 0,
              "desc": "52/17 Rule (52min work, 17min break)"},
    "90min": {"work": 90, "break": 20, "long_break": 0, "interval": 0,
              "desc": "90-minute Deep Work (90/20)"},
    "sprint": {"work": 15, "break": 3, "long_break": 10, "interval": 4,
               "desc": "Sprint (15/3, long break every 4)"},
    "custom": {"work": 25, "break": 5, "long_break": 15, "interval": 4,
               "desc": "Custom (set your own via config)"},
}


@cli.command("presets")
def presets_cmd():
    """Show available Pomodoro technique presets.

    \b
    Examples:
      pomo-pet presets                  # List all presets
      pomo-pet presets --apply classic  # Apply a preset
    """
    click.echo("Available presets:")
    for name, p in PRESETS.items():
        click.echo(f"  {name:10s}  {p['desc']}")


@cli.command("apply")
@click.argument("preset_name")
@click.pass_context
def apply_cmd(ctx, preset_name):
    """Apply a Pomodoro technique preset.

    \b
    Examples:
      pomo-pet apply classic   # 25/5 with long breaks
      pomo-pet apply 52-17     # 52/17 rule
      pomo-pet apply 90min     # 90-minute deep work
    """
    if preset_name not in PRESETS:
        click.echo(f"Unknown preset: {preset_name}. Run 'pomo-pet presets' to see options.", err=True)
        sys.exit(1)
    p = PRESETS[preset_name]
    cfg = Config.load()
    cfg.update(
        work_minutes=p["work"],
        break_minutes=p["break"],
        long_break_minutes=p["long_break"],
        long_break_interval=p["interval"],
    )
    click.echo(f"Applied '{preset_name}': {p['desc']}")
    click.echo(f"  Work: {p['work']}min | Break: {p['break']}min")
    if p["interval"] > 0:
        click.echo(f"  Long break: {p['long_break']}min every {p['interval']} sessions")


@cli.command()
def update():
    """Update Pomo Pet to the latest version."""
    import shutil

    install_dir = Path.home() / ".pomo-pet"
    if not (install_dir / ".git").exists():
        click.echo("Not installed via install.sh. Run:")
        click.echo("  curl -sSL https://raw.githubusercontent.com/someshfengde/pomo_pet/main/install.sh | bash")
        sys.exit(1)

    click.echo("Updating Pomo Pet...")

    # git pull
    result = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=install_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo(f"Git pull failed: {result.stderr.strip()}", err=True)
        sys.exit(1)
    click.echo(result.stdout.strip())

    # uv sync
    uv = shutil.which("uv")
    if not uv:
        click.echo("uv not found. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)

    result = subprocess.run(
        [uv, "sync"],
        cwd=install_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo(f"uv sync failed: {result.stderr.strip()}", err=True)
        sys.exit(1)

    click.echo("Updated! Restart pomo-pet to use the new version.")
