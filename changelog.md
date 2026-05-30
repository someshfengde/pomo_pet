# Changelog

All notable changes to Pomo Pet are documented here.

## [1.4.0] — 2026-05-29

### Fixed
- **Always-on-top broken** — rewrote `_apply_floating_level` to use PyObjC AppKit directly (old `PyObjCObject_New` approach broke in PyObjC 12+)
- **Pet hidden behind other windows** — now uses `NSStatusWindowLevel` (25) instead of `NSFloatingWindowLevel` (3), same level as status bar items and sticky note apps
- **Hide/Show broken** — re-applies window flags and floating level after `show()` with multiple delayed calls
- **Window disappears on Space switch** — `setCollectionBehavior_(CanJoinAllSpaces | Stationary)` ensures pet appears on all Spaces
- **Window hides when app deactivates** — `setHidesOnDeactivate_(False)` + `setCanHide_(False)`

### Added
- **Window position persistence** — saves/restores position from `~/.pomo-pet/config.json`
- **Move-to submenu** — right-click → Move to → Top Left / Top Right / Bottom Left / Bottom Right / Center
- **Arrow key nudge** — arrow keys move window by 20px, auto-saved
- **Pause indicator** — semi-transparent overlay with pause icon on pet sprite when paused
- **Mini/compact mode** — 📐 Mini Mode toggle in context menu (60px timer-only display)
- **Hide/Show toggle** — 🙈 Hide Pet / 👀 Show Pet in context menu
- **Celebration glow** — golden glow effect on timer text when session completes
- **Context menu timer status** — shows timer, phase, session count with emojis
- **reset-config CLI command** — `pomo-pet reset-config` restores all defaults
- **Tray integration in .app** — system tray icon with pause/reset/quit (was missing from .app entry point)
- **Skip handler in .app** — on_skip callback now works in bundled app
- **Long break notification in .app** — notify_long_break() now called
- **Better tray icon** — clean green circle with gradient, dark glass-styled menu
- **Single-click tray toggle** — click tray icon to pause/resume
- **Better tray tooltip** — emoji indicators, phase display
- **More motivational messages** — 8 work, 3 break, 3 long break new messages
- **Time-of-day greetings** — morning ☀️, afternoon 💪, evening 🌆 (25% chance)
- **Off-screen bounds check** — window position validation on restore
- **6 new integration tests** — verifies native window level is actually 25
- **7 new unit tests** — nudge, move-to, position persistence

### Changed
- Window level from `NSFloatingWindowLevel` (3) to `NSStatusWindowLevel` (25)
- Periodic re-apply interval from 2 seconds to 1 second
- Removed `Qt.Tool` flag (was causing macOS to treat window as utility panel)
- README updated with all new features, controls, and keyboard shortcuts
- install.sh updated with correct CLI usage and keyboard shortcut docs
- IMPROVEMENTS.md updated with latest feature status
- Version bumped to 1.4.0

## [1.3.0] — 2026-05-29

### Fixed
- **Streak logic bug** — consecutive daily sessions now correctly extend the streak instead of resetting to 1
- **Notification injection** — escape quotes in osascript notification messages to prevent failures
- **Config CLI path** — `pomo-pet config` now shows the actual config file path (`~/.pomo-pet/config.json`)

### Added
- **Long break support** — every 4th session triggers a 15-minute long break (configurable via `long_break_interval` and `long_break_minutes`)
- **Skip phase** — `timer.skip_phase()` to advance to the next phase immediately
- **Right-click context menu** — pause, reset, skip phase, quit (with styled dark glass menu)
- **LONG_BREAK phase** — new timer phase with distinct purple color in the UI
- **Long break messages** — dedicated motivational messages for long breaks
- **Keyboard shortcut** — `Cmd+Shift+S` to skip phase
- 10 new tests for streak logic, long breaks, skip phase, and long break messages

### Changed
- Window `paintEvent` now uses `Theme` constants instead of hardcoded colors
- README updated with new controls, features, and project structure
- Timer `_transition_if_needed` now handles BREAK → WORK and LONG_BREAK → WORK transitions

## [1.0.0] — 2026-05-10

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
