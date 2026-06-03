# 🐾 Pomo Pet

**Pomodoro timer with animated pets for desktop and the web**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-171%20Python%20%2B%209%20web-brightgreen.svg)](#testing)

Pomo Pet started as a tiny always-on-top desktop companion and now also ships as
an installable, local-first web app. The web workspace combines a Pomodoro
timer, animated pets, built-in focus tasks, Codex Pets imports, local stats,
achievements, session reflections, offline support, and PWA install metadata.

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
| Move pet | Click + drag (or arrow keys) |
| Pause / Resume | Single click (or `Cmd+Shift+P`) |
| Reset timer | Double click (or `Cmd+Shift+R`) |
| Context menu | Right-click |
| Skip phase | Right-click → Skip Phase |
| Hide/Show pet | Right-click → Hide/Show |
| Mini mode | Right-click → Mini Mode |
| Quit | `Q` / `ESC` / Right-click → Quit |

**Keyboard shortcuts:** `Cmd+Shift+P` pause · `Cmd+Shift+R` reset · `Cmd+Shift+Q` quit · Arrow keys nudge position

## Features

- **Always on top** — pet stays visible above all other windows (7-layer reliability)
- **Animated desktop pet** — floating transparent window with 9 animation states
- **Installable web app** — PWA in `docs/` with offline support, responsive workspace UI, and local stats
- **Built-in focus tasks** — add/select/complete tasks directly in the web app; selected tasks become the active focus intention
- **Pomodoro timer** — work / break / long break with progress bar
- **Smart long breaks** — every 4th session triggers a 15-minute rest (configurable)
- **Pet reactions** — animations change based on timer state, hover, dragging
- **Pause indicator** — visual overlay when timer is paused
- **Celebration glow** — golden glow effect when sessions complete
- **Mini mode** — compact timer-only display for minimal overlay
- **Sound effects** — phase changes, session completions, clicks
- **macOS notifications** — native alerts when sessions complete
- **Session statistics** — streaks, total focus time, daily counts (persisted)
- **Web review tools** — weekly chart, insights, daily goal ring, achievements, history, reflections, import/export, and share summary
- **Codex Pets support** — import custom pets from direct spritesheets, `codex-pets.net/pets/{slug}`, `share/{slug}`, or API URLs
- **Right-click menu** — timer status, pause, reset, skip, move-to, hide, mini mode, quit
- **Window position persistence** — remembers where you placed the pet
- **Move-to positions** — quick snap to corners or center
- **Custom messages** — bring your own motivational quotes via file
- **Time-of-day greetings** — morning/afternoon/evening motivational messages
- **System tray** — menu bar icon with pause/reset/quit

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

Browse [Codex Pets](https://codex-pets.net/) for compatible pet pages and
spritesheets. The web app accepts links such as
`https://codex-pets.net/pets/dario` and reads available pet metadata for correct
frame sizing.

## Development

```bash
make install    # Install dependencies
make test       # Run Python tests
make test-all   # Run with coverage
make run        # Launch with avocado
make app        # Build macOS .app bundle
make app-dmg    # Build DMG for distribution
```

## Web App / PWA

The browser version lives in `docs/` so it can deploy directly to GitHub Pages.

Public Pages URL: <https://someshfengde.github.io/pomo_pet/>

```bash
python3 -m http.server 4173 --directory docs
# Open http://127.0.0.1:4173
```

The web app is organized as a full-screen productivity workspace:

- **Focus** — large timer stage, animated pet, progress bar, focus intention, and quick intention chips.
- **Session dock** — start/reset/skip controls, presets, built-in task list, today's stats, pet bond, and break prompts.
- **Pet Lab** — bundled variants plus custom Codex Pets URLs and direct spritesheets.
- **Stats** — weekly focus chart, local insights, achievements, history, session reflections, JSON import/export, and share summary.
- **Settings** — duration controls, notification toggle, gentle tick, keep-awake, install/offline/storage readiness.

Everything is local-first: tasks, settings, stats, reflections, imported pets,
and achievements stay in browser storage unless you export/share them yourself.
The PWA also includes offline caching, install metadata, social preview tags,
structured data, a generated preview image, service worker, notification support,
browser title timer sync, and optional screen wake lock during running sessions.

Web checks are covered by:

```bash
pytest tests/test_web_pwa.py
python scripts/audit_pwa.py
npm run test:web
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
docs/
├── index.html          # Static PWA app shell
├── app.js              # Browser timer, task list, pet gallery, stats, notifications
├── styles.css          # Responsive web UI
├── assets/preview.png  # Social/install preview image
├── manifest.webmanifest
└── sw.js               # Offline service worker
scripts/
└── audit_pwa.py        # Static PWA launch/installability and repo-safety audit
```

## License

MIT
