# 🐾 Pomo Pet

**Pomodoro timer with animated desktop pets**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-156%20passed-brightgreen.svg)](#testing)

## Quick Start

```bash
# Install with Homebrew (recommended)
brew tap someshfengde/pomo-pet
brew install pomo-pet

# Or install with curl
curl -sSL https://raw.githubusercontent.com/someshfengde/pomo_pet/main/install.sh | bash

# Launch (default: avocado pet, 25min work / 5min break)
pomo-pet start

# Or pick a pet
pomo-pet start avocado
```

## Usage

```bash
pomo-pet start              # Launch default pet (avocado)
pomo-pet start avocado      # Launch specific pet
pomo-pet list               # See available pets
pomo-pet stats              # View session statistics
pomo-pet stats --format json  # Export stats as JSON
pomo-pet config             # View all config settings

# Presets
pomo-pet presets            # List Pomodoro technique presets
pomo-pet apply classic      # Apply classic 25/5 preset
pomo-pet apply 52-17        # Apply 52/17 rule preset

# Custom durations
pomo-pet --work 30 --break 10 start

# Disable sounds
pomo-pet --no-sound start

# Persistent config
pomo-pet config work_minutes 30
pomo-pet config volume 50
```

## Controls

| Action | How |
|--------|-----|
| Move pet | Click + drag |
| Pause / Resume | Single click |
| Reset timer | Double click |
| Context menu | Right-click |
| Skip phase | Right-click → Skip Phase |
| Quit | `Q` / `ESC` / Right-click → Quit |

**Keyboard shortcuts:** `Cmd+Shift+P` pause · `Cmd+Shift+R` reset · `Cmd+Shift+Q` quit

## Features

- **Animated desktop pet** — floating transparent window with 9 animation states
- **Pomodoro timer** — work / break / long break with progress bar
- **Smart long breaks** — every 4th session triggers a 15-minute rest (configurable)
- **Pet reactions** — animations change based on timer state, hover, dragging
- **Sound effects** — phase changes, session completions, clicks
- **macOS notifications** — native alerts when sessions complete
- **Session statistics** — streaks, total focus time, daily counts (persisted)
- **Right-click menu** — pause, reset, skip phase, quit
- **Custom messages** — bring your own motivational quotes via file

## Adding Pets

Create a directory under `pets/` with:

```
pets/mypet/
├── pet.json
└── spritesheet.webp
```

**pet.json:**
```json
{
  "id": "mypet",
  "displayName": "My Pet",
  "description": "A custom pet!",
  "spritesheetPath": "spritesheet.webp",
  "kind": "creature",
  "frameWidth": 192,
  "frameHeight": 192,
  "animations": {
    "idle":      { "row": 0, "frames": 6, "fps": 8,  "loop": true },
    "run_right": { "row": 1, "frames": 8, "fps": 12, "loop": true },
    "run_left":  { "row": 2, "frames": 8, "fps": 12, "loop": true },
    "waving":    { "row": 3, "frames": 4, "fps": 8,  "loop": true },
    "jumping":   { "row": 4, "frames": 5, "fps": 10, "loop": true },
    "failed":    { "row": 5, "frames": 8, "fps": 10, "loop": false },
    "waiting":   { "row": 6, "frames": 6, "fps": 6,  "loop": true },
    "running":   { "row": 7, "frames": 6, "fps": 10, "loop": true },
    "review":    { "row": 8, "frames": 6, "fps": 8,  "loop": true }
  }
}
```

Browse [Petdex](https://petdex.dev/) for spritesheet-compatible pets.

## Development

```bash
make install    # Install dependencies
make test       # Run tests (141 passing)
make test-all   # Run with coverage
make run        # Launch with avocado
make app        # Build macOS .app bundle
make app-dmg    # Build DMG for distribution
```

**Project structure:**
```
src/
├── cli.py              # Click CLI with subcommands
├── core/
│   ├── timer.py        # PomodoroTimer (pause, reset, skip, long breaks)
│   ├── messages.py     # Phase-aware messages (work, break, long break)
│   ├── stats.py        # Session statistics with streak tracking
│   └── config.py       # Persistent config (~/.pomo-pet/config.json)
├── pets/
│   ├── models.py       # Pet, AnimationDef
│   ├── loader.py       # Load from pet.json
│   └── renderer.py     # Pillow spritesheet utils
└── ui/
    ├── theme.py        # Design tokens & colors
    ├── window.py       # PySide6 window, animations, context menu
    ├── sounds.py       # Sound effects (macOS afplay)
    ├── notifications.py # macOS native notifications
    └── tray.py         # System tray integration
```

## License

MIT
