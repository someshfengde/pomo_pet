
# 🐾 POMO PET

### *A Pomodoro Timer with Adorable Animated Desktop Pets*

**Focus Better. Break Smarter. Pet Your Way to Productivity.**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-91%20passed-brightgreen.svg)](#-under-the-hood)
[![Made with PySide6](https://img.shields.io/badge/Made%20with-PySide6-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)

</div>

---

> 📖 *This README is a comic. Each "chapter" tells part of the Pomo Pet story.*
> *Read top to bottom, like a manga — or skip to [Installation](#-get-started) if you're impatient.*

---

## 📕 Chapter 1: The Problem

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   NARRATOR BOX                                   │
│   ─────────────                                  │
│   It's 3:00 PM. Nobita has a deadline at 5.      │
│   He opens his laptop. He's going to focus.      │
│   This time will be different.                   │
│                                                  │
└──────────────────────────────────────────────────┘
```

```
  ┌─────────────────────┐     ┌─────────────────────┐
  │  📱 "Oh! A message!" │     │  ⏰ 4:30 PM          │
  │                      │     │                      │
  │     😵‍💫               │     │  Two hours later...  │
  │   (scrolling...)     │     │  Nothing done.       │
  │                      │     │                      │
  └─────────────────────┘     └─────────────────────┘

              ┌─────────────────────────┐
              │                         │
              │   😤 "I can't focus...  │
              │   there HAS to be a     │
              │   better way!"          │
              │                         │
              └─────────────────────────┘
```

**Sound familiar?** Distractions win. Timers feel cold. You need something *alive* to keep you accountable.

---

## 📗 Chapter 2: Meet the Pet

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   ✨ GADGET REVEAL ✨                             │
│                                                  │
│   From the 4D pocket... a companion appears!     │
│                                                  │
└──────────────────────────────────────────────────┘
```

```
                    ╭───────────╮
                   ╱    🌿      ╲
                  │   ╭─────╮    │
                  │   │ ● ● │    │
                  │   │  ▽  │    │      "Hi! I'm your
                  │   ╰─────╯    │       new focus buddy!"
                  │   ┌─────┐    │
                  │   │█████│    │
                  │   │█████│    │
                   ╲  └─────┘   ╱
                    ╰───────────╯
                     AVOCADO PET
```

**Pomo Pet** is a Pomodoro timer with an animated desktop companion that lives on your screen.

| What it does | How it feels |
|:-------------|:-------------|
| ⏱️ Runs 25min work / 5min break cycles | Like having a study buddy |
| 🎬 Animates based on what you're doing | The pet *reacts* to you |
| 🖱️ Follows your mouse when you drag it | Alive, not just a timer |
| 💬 Shows motivational messages | Contextual to work/break phase |
| 📊 Tracks sessions with gold dots | Satisfying visual progress |

---

## 📘 Chapter 3: The Controls

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   NARRATOR BOX                                   │
│   ─────────────                                  │
│   The pet responds to your touch.                │
│   Every gesture means something.                 │
│                                                  │
└──────────────────────────────────────────────────┘
```

```
  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
  │                 │   │                 │   │                 │
  │   👆 CLICK      │   │   👆👆 DBL-CLICK │   │   ✋ DRAG        │
  │                 │   │                 │   │                 │
  │   ⏸️  Pause      │   │   🔄 Reset      │   │   🏃 Pet follows │
  │   ▶️  Resume     │   │   timer         │   │   your cursor!  │
  │                 │   │                 │   │                 │
  └─────────────────┘   └─────────────────┘   └─────────────────┘
```

| Action | What happens |
|:-------|:-------------|
| **Click** the pet | ⏸️ Toggle pause / ▶️ resume |
| **Double-click** the pet | 🔄 Reset the current timer |
| **Drag** anywhere | 🏃 Pet runs in that direction! |
| **Press Q or ESC** | 👋 Quit |

### The Timer UI

```
  ┌─────────────────────────────────────┐
  │                                     │
  │          24:37                      │
  │   ══════════════░░░░░░░░░          │
  │                                     │
  │   WORK  ● ● ● ○ ○ ○ ○ ○           │
  │                                     │
  │          ╭─────────╮               │
  │          │  🥑     │               │
  │          │ running │               │
  │          │  state  │               │
  │          ╰─────────╯               │
  │                                     │
  │        "Stay focused!"              │
  │                                     │
  └─────────────────────────────────────┘
       Frosted glass · Dark minimal · macOS vibes
```

---

## 📙 Chapter 4: Animation States

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   NARRATOR BOX                                   │
│   ─────────────                                  │
│   The pet has 9 animation states.                │
│   It knows what you're doing.                    │
│                                                  │
└──────────────────────────────────────────────────┘
```

```
   idle          run →         run ←         waving
  ╭─────╮      ╭─────╮       ╭─────╮       ╭─────╮
  │ ● ● │      │ ●>● │       │ ●●< │       │ ● ● │  ✋
  │  -  │      │ >>> │       │ <<< │       │  ▽  │
  ╰──┬──╯      ╰──┬──╯       ╰──┬──╯       ╰──┬──╯
   😴            🏃💨           💨🏃           😊

  jumping       failed        waiting       running       review
  ╭─────╮      ╭─────╮       ╭─────╮       ╭─────╮       ╭─────╮
  │ ● ● │  ↑   │ ✖ ✖ │       │ ● ● │       │ ●>● │       │ ● ● │
  │  ▽  │      │  ~  │       │  z  │       │ >>> │       │  ◔  │
  ╰──┬──╯      ╰──┬──╯       ╰──┬──╯       ╰──┬──╯       ╰──┬──╯
   🎉            💀            💤            💪            🤔
```

| State | When | Row | Frames |
|:------|:-----|:----|:-------|
| `idle` | Break phase, default | 0 | 6 |
| `run_right` | Dragging right → | 1 | 8 |
| `run_left` | Dragging left ← | 2 | 8 |
| `waving` | Available | 3 | 4 |
| `jumping` | Available | 4 | 5 |
| `failed` | Available | 5 | 8 |
| `waiting` | Available | 6 | 6 |
| `running` | Work phase | 7 | 6 |
| `review` | Available | 8 | 6 |

---

## 📒 Chapter 5: Add Your Own Pet

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   NARRATOR BOX                                   │
│   ─────────────                                  │
│   Want a custom pet? It takes 3 steps.           │
│   Doraemon shows you how.                        │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Step 1: Create the directory

```
  pets/
    mypet/
      pet.json          ← animation definitions
      spritesheet.webp  ← your pet's animations
```

### Step 2: Define `pet.json`

```json
{
  "id": "mypet",
  "displayName": "My Pet",
  "description": "A custom pet!",
  "spritesheetPath": "spritesheet.webp",
  "frameWidth": 192,
  "frameHeight": 192,
  "animations": {
    "idle":      { "row": 0, "frames": 6, "fps": 8,  "loop": true },
    "run_right": { "row": 1, "frames": 8, "fps": 12, "loop": true },
    "run_left":  { "row": 2, "frames": 8, "fps": 12, "loop": true },
    "waving":    { "row": 3, "frames": 4, "fps": 8,  "loop": true },
    "jumping":   { "row": 4, "frames": 5, "fps": 10, "loop": true },
    "running":   { "row": 7, "frames": 6, "fps": 10, "loop": true }
  }
}
```

### Step 3: Get a spritesheet

```
  ┌─────────────────────────────────────────────┐
  │  SPRITESHEET LAYOUT (192×192 per frame)     │
  │                                             │
  │  ┌────┬────┬────┬────┬────┬────┬────┬────┐  │
  │  │ f0 │ f1 │ f2 │ f3 │ f4 │ f5 │    │    │  │  Row 0: idle
  │  ├────┼────┼────┼────┼────┼────┼────┼────┤  │
  │  │ f0 │ f1 │ f2 │ f3 │ f4 │ f5 │ f6 │ f7 │  │  Row 1: run_right
  │  ├────┼────┼────┼────┼────┼────┼────┼────┤  │
  │  │ f0 │ f1 │ f2 │ f3 │ f4 │ f5 │ f6 │ f7 │  │  Row 2: run_left
  │  ├────┼────┼────┼────┼────┼────┼────┼────┤  │
  │  │ f0 │ f1 │ f2 │ f3 │    │    │    │    │  │  Row 3: waving
  │  └────┴────┴────┴────┴────┴────┴────┴────┘  │
  │       ... 9 rows total, 8 columns max       │
  └─────────────────────────────────────────────┘
```

> 💡 **Tip:** Browse [Petdex](https://petdex.dev/) for ready-made spritesheets. Look for the "Install" button!

**Tools to create spritesheets:** [Aseprite](https://www.aseprite.org/) · [LibreSprite](https://libresprite.github.io/) · [Petdex](https://petdex.dev/)

**Format:** WebP with transparency · 192×192 px frames · One animation per row

---

## 📓 Chapter 6: Under the Hood

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   NARRATOR BOX                                   │
│   ─────────────                                  │
│   Built with modern Python tools.                │
│   91 tests. All green. ✅                        │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Tech Stack

```
  ┌─────────────────────────────────────┐
  │           POMO PET                  │
  ├─────────────────────────────────────┤
  │  ┌───────────────────────────────┐  │
  │  │         PySide6 (Qt)          │  │  ← Window, drag, paint, animation
  │  │  ┌─────────────────────────┐  │  │
  │  │  │   Pillow (sprites)      │  │  │  ← Spritesheet decoding
  │  │  │  ┌───────────────────┐  │  │  │
  │  │  │  │  Click (CLI)      │  │  │  │  ← Command-line interface
  │  │  │  │  ┌─────────────┐  │  │  │  │
  │  │  │  │  │  uv (pack)  │  │  │  │  │  ← Fast Python packaging
  │  │  │  │  └─────────────┘  │  │  │  │
  │  │  │  └───────────────────┘  │  │  │
  │  │  └─────────────────────────┘  │  │
  │  └───────────────────────────────┘  │
  └─────────────────────────────────────┘
```

| Layer | Technology | What it does |
|:------|:-----------|:-------------|
| 🖥️ Window | [PySide6](https://doc.qt.io/qtforpython-6/) (Qt) | Frameless window, per-pixel transparency, native dragging |
| 🖼️ Sprites | [Pillow](https://python-pillow.org/) | Spritesheet decoding, frame extraction |
| ⌨️ CLI | [Click](https://click.palletsprojects.com/) | `pomo-pet --pet avocado --work 30 --break 10` |
| 📦 Packaging | [uv](https://docs.astral.sh/uv/) | Fast dependency resolution |
| 🧪 Testing | [pytest](https://pytest.org/) | 91 tests, all passing ✅ |

### Project Structure

```
  pomo_pet/
  ├── src/
  │   ├── cli.py              ← Click CLI entry point
  │   ├── timer.py            ← Pomodoro timer with pause/reset
  │   ├── pet_loader.py       ← Load pets + animations from JSON
  │   ├── pet_renderer.py     ← Pillow spritesheet utilities
  │   ├── pet_window.py       ← PySide6 window (drag, paint, anim)
  │   └── messages.py         ← Phase-aware motivational messages
  ├── tests/
  │   ├── test_timer.py       ← 24 tests
  │   ├── test_pet_loader.py  ← 12 tests
  │   ├── test_pet_window.py  ← 27 tests
  │   ├── test_messages.py    ← 6 tests
  │   ├── test_cli.py         ← 12 tests
  │   └── test_integration.py ← 10 tests
  └── pets/
      └── avacado/
          ├── pet.json
          └── spritesheet.webp
```

### Run Tests

```bash
make test        # Run all tests
make test-all    # Run with coverage
```

---

## 📕 Epilogue: Get Started

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   NARRATOR BOX                                   │
│   ─────────────                                  │
│   From distraction to determination.             │
│   One pet at a time.                             │
│                                                  │
└──────────────────────────────────────────────────┘
```

```
  ┌─────────────────────────────────────┐
  │                                     │
  │          04:58                      │
  │   ════════════════════░░░░         │
  │                                     │
  │   WORK  ● ● ● ● ● ● ● ○           │
  │                                     │
  │          ╭─────────╮               │
  │          │  🥑     │               │
  │          │  idle   │               │
  │          ╰─────────╯               │
  │                                     │
  │    "Great job! Take a break."       │
  │                                     │
  └─────────────────────────────────────┘
```

### Quick Start

```bash
git clone https://github.com/yourusername/pomo-pet.git
cd pomo-pet
make install
```

### Launch

```bash
# List available pets
pomo-pet --list-pets

# Start with the avocado pet
pomo-pet --pet avocado

# Custom durations
pomo-pet --pet avocado --work 30 --break 10
```

### All Options

```
Usage: pomo-pet [OPTIONS]

Options:
  --pet TEXT       Pet to display (e.g., avocado)
  --work INTEGER   Work session duration in minutes (default: 25)
  --break INTEGER  Break session duration in minutes (default: 5)
  --list-pets      List all available pets
  --help           Show this message and exit.
```

---

<div align="center">

### 🐾 Ready to focus?

```
         ╭─────────╮
         │  🥑     │
         │  ~ * ~  │    ← The pet believes in you.
         ╰────┬────╯
              │
         ╭────┴────╮
         │  FOCUS  │
         ╰─────────╯
```

**Made with 🥑 and ☕**

*Pets are user-submitted fan art. Inspired by [Petdex](https://petdex.dev/).*

[MIT License](LICENSE) · Python 3.13+ · macOS · Linux · Windows

</div>
]]>
