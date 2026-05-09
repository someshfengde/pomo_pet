<![CDATA[<div align="center">

# 🐾 Pomo Pet

**A Pomodoro timer with animated desktop pets**

*Focus better. Break smarter. Pet your way to productivity.*

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-109%20passed-brightgreen.svg)](#testing)
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

[Features](#features) · [Install](#installation) · [Usage](#usage) · [Controls](#controls) · [Add Pets](#adding-pets) · [Development](#development)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎬 **Animated Pets** | 9 animation states from Petdex-compatible spritesheets |
| 🖱️ **Drag to Move** | Grab and drag your pet anywhere on screen |
| ➡️ **Direction Reactions** | Drag left → run left. Drag right → run right. |
| ⏱️ **Pomodoro Timer** | 25min work / 5min break (customizable) |
| 📊 **Progress Bar** | Gradient bar fills as time passes |
| ⏸️ **Click to Pause** | Single click toggles pause/play |
| 🔄 **Double-Click Reset** | Double click resets current timer |
| 🎭 **Smart Animations** | Pet reacts to timer events automatically |
| 💬 **Motivational Messages** | Phase-aware messages change with work/break |
| 🎯 **Session Tracking** | Gold dots track completed pomodoros |
| 🌙 **Frosted Glass UI** | Dark, minimal, transparent floating window |
| 🔔 **Desktop Notifications** | Native macOS notifications on timer events |
| 🔊 **Sound Effects** | Subtle sounds for phase changes and completions |
| 📈 **Session Statistics** | Track total sessions, focus time, streaks |

## 🚀 Installation

### One-liner (curl)

```bash
curl -sSL https://raw.githubusercontent.com/someshfengde/pomo_pet/main/install.sh | bash
```

### Manual

```bash
git clone https://github.com/someshfengde/pomo_pet.git
cd pomo_pet
make install
```

## 🎮 Usage

```bash
# List available pets
pomo-pet --list-pets

# Launch with defaults (25min work / 5min break)
pomo-pet --pet avocado

# Custom durations
pomo-pet --pet avocado --work 30 --break 10

# View session statistics
pomo-pet --stats

# Launch without sound
pomo-pet --pet avocado --no-sound
```

## 🕹️ Controls

| Action | How |
|--------|-----|
| **Move pet** | Click and drag |
| **Pause / Resume** | Single click |
| **Reset timer** | Double click |
| **Quit** | `Q` or `ESC` |

## 🎭 Animation States

Animations trigger automatically based on context:

| State | Trigger | Row | Frames |
|-------|---------|-----|--------|
| `idle` | Break phase | 0 | 6 |
| `run_right` | Drag right | 1 | 8 |
| `run_left` | Drag left | 2 | 8 |
| `waving` | Session complete | 3 | 4 |
| `jumping` | Phase transition | 4 | 5 |
| `failed` | Timer hits 00:00 | 5 | 8 |
| `waiting` | 30s idle | 6 | 6 |
| `running` | Work phase | 7 | 6 |
| `review` | Work phase (alters) | 8 | 6 |

## 📈 Statistics

View your productivity stats:

```bash
pomo-pet --stats
```

```
Total sessions:   42
Total focus:      17.5h (1050min)
Total break:      210min
Current streak:   5
Best streak:      12
Today:            3 sessions
```

Stats are saved to `~/.pomo-pet/stats.json` and persist across sessions.

## 🐉 Adding Pets

### 1. Create directory

```
pets/mypet/
├── pet.json
└── spritesheet.webp
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

### 3. Spritesheet format

- **Format:** WebP with transparency
- **Frame size:** 192×192 px (recommended)
- **Layout:** One animation per row
- **Tools:** [Aseprite](https://www.aseprite.org/), [Petdex](https://petdex.dev/)

## 🛠️ Development

### Commands

```bash
make install    # Install dependencies
make test       # Run tests
make test-all   # Run tests with coverage
make run        # Launch with avocado pet
```

### Project Structure

```
pomo_pet/
├── src/
│   ├── __init__.py         # Public API re-exports
│   ├── __main__.py         # python -m src
│   ├── cli.py              # Click CLI + wiring
│   ├── core/
│   │   ├── timer.py        # PomodoroTimer, pause/reset
│   │   ├── messages.py     # Phase-aware messages
│   │   └── stats.py        # Session statistics
│   ├── pets/
│   │   ├── models.py       # Pet, AnimationDef
│   │   ├── loader.py       # load_pet(), list_pets()
│   │   └── renderer.py     # Pillow spritesheet utils
│   └── ui/
│       ├── theme.py        # Colors, fonts, config
│       ├── window.py       # PySide6 window + animations
│       ├── sounds.py       # Sound effects (macOS afplay)
│       └── notifications.py # Desktop notifications
├── assets/
│   └── sounds/             # Generated WAV sound files
├── tests/                  # 109 tests
├── pets/
│   └── avacado/
│       ├── pet.json
│       └── spritesheet.webp
├── pyproject.toml
├── Makefile
├── install.sh
├── CHANGELOG.md
└── README.md
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| CLI | [Click](https://click.palletsprojects.com/) |
| Window | [PySide6](https://doc.qt.io/qtforpython-6/) (Qt) |
| Sprites | [Pillow](https://python-pillow.org/) |
| Sound | macOS `afplay` (no deps) |
| Notifications | macOS `osascript` (no deps) |
| Testing | [pytest](https://pytest.org/) |
| Packaging | [uv](https://docs.astral.sh/uv/) |

## 📝 License

MIT

---

<div align="center">

**Made with 🥑 and ☕**

*Inspired by [Petdex](https://petdex.dev/)*

</div>
]]>