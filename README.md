# 🐾 Pomo Pet

**Pomodoro timer with animated desktop pets**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-120%20passed-brightgreen.svg)](#testing)

## Quick Start

```bash
# Install
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

# Custom durations
pomo-pet --work 30 --break 10 start

# Disable sounds
pomo-pet --no-sound start
```

## Controls

| Action | How |
|--------|-----|
| Move pet | Click + drag |
| Pause / Resume | Single click |
| Reset timer | Double click |
| Quit | `Q` or `ESC` |

## What It Does

- Floating transparent window with animated pet sprite
- Pomodoro timer with progress bar
- Pet animations react to timer state (work, break, idle, dragging)
- Sound effects on phase changes and session completions
- macOS native notifications
- Session statistics persisted across runs

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
make test       # Run tests (120 passing)
make test-all   # Run with coverage
make run        # Launch with avocado
```

**Project structure:**
```
src/
├── cli.py              # Click CLI with subcommands
├── core/
│   ├── timer.py        # PomodoroTimer (pause, reset)
│   ├── messages.py     # Phase-aware messages
│   └── stats.py        # Session statistics
├── pets/
│   ├── models.py       # Pet, AnimationDef
│   ├── loader.py       # Load from pet.json
│   └── renderer.py     # Pillow spritesheet utils
└── ui/
    ├── theme.py        # Design tokens
    ├── window.py       # PySide6 window + animations
    ├── sounds.py       # Sound effects
    └── notifications.py # macOS notifications
```

## License

MIT
