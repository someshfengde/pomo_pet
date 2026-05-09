# Changelog

All notable changes to Pomo Pet are documented here.

## [0.1.0] — 2026-05-10

### Added

#### Core Application
- Python CLI built with Click (`pomo-pet` command)
- `uv` package management with `pyproject.toml`
- `Makefile` with `install`, `test`, `test-all`, `run` targets
- Entry points: `pomo-pet --pet avocado` and `python -m src`

#### Timer (`src/timer.py`)
- Pomodoro timer with configurable work/break durations (default 25/5)
- Phase tracking: WORK → BREAK → WORK cycle
- Session counting (increments on work phase completion)
- Pause/resume toggle (`timer.toggle_pause()`)
- Reset to current phase start (`timer.reset()`)
- MM:SS formatting (`timer.format_remaining()`)
- Tick respects paused state (no-op when paused)

#### Pet System (`src/pet_loader.py`)
- Load pets from `pets/` directory structure
- `pet.json` metadata: id, displayName, description, spritesheetPath, kind
- Animation definitions: frameWidth, frameHeight, per-animation fps/loop/frames
- `AnimationDef` dataclass for animation state definitions
- `list_pets()` discovers all valid pets in a directory
- Error handling: missing JSON, missing spritesheet, invalid JSON, missing fields

#### Window (`src/pet_window.py`)
- PySide6 (Qt) frameless, transparent, always-on-top window
- Native macOS dragging via `Qt.FramelessWindowHint`
- Frosted dark glass design (no borders, no close button)
- Timer text with gradient progress bar (green=work, blue=break)
- Phase label + session dots (gold filled / dark empty)
- Pet name + current animation label
- Motivational message bar with slide-in animation
- Paused overlay with "⏸ PAUSED" and hint text

#### Animation System
- 9 animation states loaded from Petdex-compatible spritesheets
- One-shot system: `_play_once()` plays animation then returns to phase default
- Phase-based auto-switching:
  - WORK → running/review (alternates every 10s)
  - BREAK → idle (switches to waiting after 30s idle)
- Event triggers:
  - Session complete → waving (one-shot)
  - Phase transition → jumping (one-shot)
  - Timer expire → failed (one-shot)
  - 30s idle → waiting (loop)
  - 10s work → running/review alternation
- Drag direction mapping:
  - Drag left → run_left animation
  - Drag right → run_right animation
  - Release → return to phase animation
- Per-animation FPS and loop behavior from pet.json

#### Gestures
- Single click → toggle pause/resume
- Double click → reset timer
- Drag (hold + move) → move window + direction animation
- Drag threshold (5px) prevents accidental pause on drag
- Q or ESC → quit

#### Messages (`src/messages.py`)
- Phase-aware motivational messages
- Work messages: "Focus time!", "Stay sharp!", etc.
- Break messages: "Take a break!", "Rest your eyes!", etc.
- Extensible `MessageProvider` with custom message support

#### Spritesheet Rendering (`src/pet_renderer.py`)
- Pillow-based spritesheet loading
- Frame extraction from grid layout
- Support for variable frame sizes

#### CLI (`src/cli.py`)
- `--pet <name>` select pet by id
- `--work <minutes>` custom work duration
- `--break <minutes>` custom break duration
- `--list-pets` show all available pets
- Timer getter returns 6 values: remaining, phase, sessions, message, progress, paused
- Action callbacks: on_toggle_pause, on_reset

#### Testing
- 98 tests across 7 test files
- TDD approach (Red-Green-Refactor for every module)
- pytest with coverage (79% overall)
- Unit tests: timer, pet_loader, messages, pet_window, pet_renderer
- CLI tests: argument parsing, window launching, timer getter, callbacks
- Integration tests: full workflow, real pet loading, timer lifecycle

#### Documentation
- README with ASCII art widget mockup
- Features table, installation guide, usage examples
- Controls table, animation states table
- Adding pets guide with JSON template
- Development section with project structure

### Dependencies
- Python 3.13+
- Click 8.0+ (CLI)
- PySide6 6.11+ (window/rendering)
- Pillow 10.0+ (spritesheet loading)
- pytest 9.0+ / pytest-cov 7.1+ (testing)
- uv (package management)
