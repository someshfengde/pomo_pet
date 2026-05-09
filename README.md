<![CDATA[<div align="center">

# 🐾 Pomo Pet

**A Pomodoro timer with adorable animated desktop pets**

*Focus better. Break smarter. Pet your way to productivity.*

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-91%20passed-brightgreen.svg)](#testing)
[![Made with PySide6](https://img.shields.io/badge/Made%20with-PySide6-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)

<br/>

```
┌─────────────────────────────┐
│   24:37                     │
│   ══════════════░░░░░░░░░   │
│   WORK  ● ● ● ○ ○ ○ ○ ○    │
│                             │
│         ┌─────────┐         │
│         │  🥑     │         │
│         │ animated│         │
│         │  pet    │         │
│         └─────────┘         │
│                             │
│       "Stay focused!"       │
└─────────────────────────────┘
```

<br/>

[Features](#features) · [Install](#installation) · [Usage](#usage) · [Add Pets](#adding-pets) · [Development](#development)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎬 **Animated Pets** | Spritesheet-driven animations with 9 states (idle, running, waving, jumping...) |
| 🖱️ **Drag to Move** | Grab your pet and drag it anywhere on screen |
| ➡️ **Direction Reactions** | Drag left → pet runs left. Drag right → pet runs right. |
| ⏱️ **Pomodoro Timer** | 25min work / 5min break (customizable via CLI) |
| 📊 **Progress Bar** | Gradient progress bar that fills as time passes |
| ⏸️ **Click to Pause** | Single click toggles pause/play |
| 🔄 **Double-Click Reset** | Double click resets the current timer |
| 💬 **Motivational Messages** | Phase-aware messages that change with work/break |
| 🎯 **Session Tracking** | Gold dots track completed pomodoro sessions |
| 🌙 **Frosted Glass UI** | Dark, minimal, macOS-inspired design |

## 🚀 Installation

### Prerequisites

- Python 3.13+
- macOS, Linux, or Windows

### Quick Start

```bash
git clone https://github.com/yourusername/pomo-pet.git
cd pomo-pet
make install
```

Or manually:

```bash
uv sync
uv pip install -e .
```

## 🎮 Usage

### List available pets

```bash
pomo-pet --list-pets
```

```
Available pets:
  avocado      - Avocado: A cute avocado Codex pet with a warm, hand-painted storybook animation feeling.
```

### Launch a pet

```bash
pomo-pet --pet avocado
```

### Custom timer durations

```bash
pomo-pet --pet avocado --work 30 --break 10
```

### All options

```
Usage: pomo-pet [OPTIONS]

Options:
  --pet TEXT       Pet to display (e.g., avocado)
  --work INTEGER   Work session duration in minutes (default: 25)
  --break INTEGER  Break session duration in minutes (default: 5)
  --list-pets      List all available pets
  --help           Show this message and exit.
```

## 🕹️ Controls

| Action | How |
|--------|-----|
| **Move pet** | Click and drag anywhere |
| **Pause / Resume** | Single click on the pet |
| **Reset timer** | Double click on the pet |
| **Quit** | Press `Q` or `ESC` |

## 🎭 Animation States

The pet automatically switches animations based on context:

| State | When | Spritesheet Row |
|-------|------|-----------------|
| `idle` | Break phase, default | Row 0 · 6 frames |
| `run_right` | Dragging right | Row 1 · 8 frames |
| `run_left` | Dragging left | Row 2 · 8 frames |
| `waving` | Available | Row 3 · 4 frames |
| `jumping` | Available | Row 4 · 5 frames |
| `failed` | Available | Row 5 · 8 frames |
| `waiting` | Available | Row 6 · 6 frames |
| `running` | Work phase | Row 7 · 6 frames |
| `review` | Available | Row 8 · 6 frames |

## 🐉 Adding Pets

### 1. Create a pet directory

```
pets/
  mypet/
    pet.json
    spritesheet.webp
```

### 2. Write `pet.json`

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

### 3. Create your spritesheet

- **Format:** WebP with transparency
- **Frame size:** 192×192 pixels (recommended)
- **Layout:** One animation per row
- **Tool:** [Aseprite](https://www.aseprite.org/), [LibreSprite](https://libresprite.github.io/), or [Petdex](https://petdex.dev/)

### 4. Submit a PR

Fork → Add your pet → Pull request!

> 💡 **Tip:** Browse [Petdex](https://petdex.dev/) for spritesheet-compatible pets. Look for the "Install" button and grab the spritesheet!

## 🛠️ Development

### Run tests

```bash
make test
```

### Run with coverage

```bash
make test-all
```

### Project structure

```
pomo_pet/
├── src/
│   ├── cli.py              # Click CLI entry point
│   ├── timer.py            # Pomodoro timer with pause/reset
│   ├── pet_loader.py       # Load pets + animations from JSON
│   ├── pet_renderer.py     # Pillow spritesheet utilities
│   ├── pet_window.py       # PySide6 window (drag, paint, anim)
│   └── messages.py         # Phase-aware motivational messages
├── tests/
│   ├── test_timer.py       # 24 tests
│   ├── test_pet_loader.py  # 12 tests
│   ├── test_pet_window.py  # 27 tests
│   ├── test_messages.py    # 6 tests
│   ├── test_cli.py         # 12 tests
│   └── test_integration.py # 10 tests
├── pets/
│   └── avacado/
│       ├── pet.json
│       └── spritesheet.webp
├── pyproject.toml
├── Makefile
└── README.md
```

### Tech stack

| Layer | Technology |
|-------|-----------|
| CLI | [Click](https://click.palletsprojects.com/) |
| Window | [PySide6](https://doc.qt.io/qtforpython-6/) (Qt) |
| Sprites | [Pillow](https://python-pillow.org/) |
| Testing | [pytest](https://pytest.org/) |
| Packaging | [uv](https://docs.astral.sh/uv/) |

## 📝 License

MIT

---

<div align="center">

**Made with 🥑 and ☕**

*Pets are user-submitted fan art. Inspired by [Petdex](https://petdex.dev/).*

</div>
]]>