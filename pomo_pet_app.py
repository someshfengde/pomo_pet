#!/usr/bin/env python3
"""Pomo Pet — macOS native application entry point.

This is the entry point for the PyInstaller-bundled macOS .app.
It initializes the Qt application with proper macOS lifecycle,
loads the default pet from config, and launches the pet window.
"""

import os
import sys
import time
from pathlib import Path

# CRITICAL: Set process name BEFORE any Qt imports — macOS reads argv[0]
sys.argv[0] = "Pomo Pet"

# Resolve paths for bundled app vs development
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    # Running as a PyInstaller bundle
    # sys._MEIPASS is where PyInstaller extracts data files
    _BUNDLE_DIR = Path(sys._MEIPASS)
    _ASSETS_DIR = _BUNDLE_DIR / "assets"
    _PETS_DIR = _BUNDLE_DIR / "pets"
    # Source code is compiled into the bundle, importable directly
else:
    # Running in development
    _BASE_DIR = Path(__file__).parent
    _ASSETS_DIR = _BASE_DIR / "assets"
    _PETS_DIR = _BASE_DIR / "pets"
    sys.path.insert(0, str(_BASE_DIR))

# Now safe to import Qt and app modules
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QTimer

from src.pets.loader import list_pets
from src.core.timer import PomodoroTimer, TimerPhase
from src.core.messages import get_message
from src.core.stats import StatsStore
from src.core.config import Config
from src.ui.window import PetWindow
from src.ui.sounds import play_phase_change, play_session_complete, play_click, set_volume
from src.ui.notifications import notify_session_complete, notify_break_over


def _set_macos_app_identity() -> None:
    """Configure macOS app identity — dock name, icon, activation policy."""
    try:
        import AppKit
        AppKit.NSProcessInfo.processInfo().setProcessName_("Pomo Pet")
        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
        # Set the app menu title
        main_menu = app.mainMenu()
        if main_menu and main_menu.itemAtIndex_(0):
            main_menu.itemAtIndex_(0).setTitle_("Pomo Pet")
    except Exception:
        pass


def _create_app_icon(pet) -> QIcon:
    """Create app icon from the pet's first idle frame."""
    icon_path = Path(pet.spritesheet_path)
    if icon_path.exists():
        sheet = QPixmap(str(icon_path))
        if not sheet.isNull():
            frame = sheet.copy(0, 0, pet.frame_width, pet.frame_height)
            return QIcon(frame)
    return QIcon()


def main() -> None:
    """Launch Pomo Pet as a macOS application."""
    # Load config
    cfg = Config.load()
    set_volume(cfg.volume if cfg.sound_enabled else 0)

    # Load pets from bundled resources
    print(f"Loading pets from: {_PETS_DIR}", file=sys.stderr)
    pets = list_pets(_PETS_DIR)
    if not pets:
        print(f"No pets found in {_PETS_DIR}!", file=sys.stderr)
        # Fallback: try the development path
        dev_pets = Path(__file__).parent / "pets" if not getattr(sys, "frozen", False) else _PETS_DIR
        pets = list_pets(dev_pets)
        if not pets:
            print("No pets found anywhere!", file=sys.stderr)
            sys.exit(1)

    # Find the default pet
    pet = next((p for p in pets if p.id == cfg.default_pet), pets[0])

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Pomo Pet")
    app.setApplicationDisplayName("Pomo Pet")
    app.setQuitOnLastWindowClosed(False)  # Keep running when window closes

    # Set icon
    icon = _create_app_icon(pet)
    app.setWindowIcon(icon)

    # macOS identity (dock name, menu)
    _set_macos_app_identity()

    # Initialize timer and state
    timer = PomodoroTimer(work_minutes=cfg.work_minutes, break_minutes=cfg.break_minutes)
    store = StatsStore()
    current_message = get_message(timer.phase)
    last_phase = timer.phase
    last_sessions = timer.sessions_completed
    last_tick = time.time()

    # Timer getter callback for the window
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
                if cfg.sound_enabled:
                    play_phase_change()
                if timer.phase == TimerPhase.WORK:
                    notify_break_over()
                last_phase = timer.phase
            if timer.sessions_completed > last_sessions:
                store.record_session(cfg.work_minutes, cfg.break_minutes)
                if cfg.sound_enabled:
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
        if cfg.sound_enabled:
            play_click()

    def on_reset():
        nonlocal current_message, last_phase
        timer.reset()
        current_message = get_message(timer.phase)
        last_phase = timer.phase
        if cfg.sound_enabled:
            play_click()

    # Create and show the pet window
    window = PetWindow(pet=pet)
    window.run(timer_getter=timer_getter, on_toggle_pause=on_toggle_pause, on_reset=on_reset)

    # Show stats in console if any
    if store.stats.total_sessions > 0:
        print(f"Pomo Pet — {store.summary}")

    # Run the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
