# Pomo Pet — Improvement Roadmap

A prioritized list of improvements to make Pomo Pet a truly delightful, Apple-quality tool.

---

## 🔴 P0 — Critical (fix now)

### 1. Window transparency broken on macOS
- **DONE** — Use `NSWindow.setOpaque_(False)` via ctypes in `showEvent`
- Fixed in `src/ui/window.py` with `_apply_macos_fixes()`

### 2. Always-on-top unreliable
- **DONE** — Use `NSWindow.setLevel_(NSFloatingWindowLevel)` via ctypes
- Replaces hacky `raise_()` timer
- **Enhanced:** Periodic re-application every 2s, app state change handler, screen/Space change handler
- **Enhanced:** `setCollectionBehavior_(CanJoinAllSpaces | Stationary)` for all Spaces support
- **Enhanced:** `orderFrontRegardless()` + visibility checks (deminiaturize, make visible)
- **Enhanced:** Cached ctypes helpers for performance

### 3. Pet sprite rendering quality
- `smoothscale` can produce blurry output on retina displays
- **Fix:** Load at 2x resolution, use `Qt.KeepAspectRatioByExpanding`, let Qt handle retina scaling

### 3b. Window position persistence
- **DONE** — Window position saved to `~/.pomo-pet/config.json` on drag
- Restored on next launch
- "📍 Reset Position" option in right-click context menu

### 3c. UI readability backdrop
- **DONE** — Semi-transparent dark backdrop pill behind timer/dots/message area
- Ensures text is readable against any desktop wallpaper

### 3d. Pause indicator overlay
- **DONE** — When timer is paused, shows semi-transparent overlay with pause icon on pet
- Clear visual feedback that the timer is paused

### 3e. Mini/compact mode
- **DONE** — 📐 Mini Mode toggle in context menu
- Shows only timer text with dark backdrop (60px tall)
- Useful for minimal overlay during focused work

### 3f. Celebration glow effect
- **DONE** — Golden glow on timer text when session completes
- Fades over 2 seconds, visual reward for completing a pomodoro

---

## 🟡 P1 — High Priority (next sprint)

### 4. Menu bar integration (macOS)
- **DONE** — `QSystemTrayIcon` with Pause/Reset/Quit menu
- Tooltip shows timer + phase
- Fixed in `src/ui/tray.py`
- **Enhanced:** Clean green circle icon with gradient highlight, dark glass-styled menu
- **Enhanced:** Single-click on tray icon toggles pause/resume

### 5. Global keyboard shortcuts
- **DONE** — `Cmd+Shift+P` pause, `Cmd+Shift+R` reset, `Cmd+Shift+Q` quit
- Uses `QShortcut` with `QKeySequence("Ctrl+Shift+…")` (maps to Cmd on macOS)
- **Enhanced:** Arrow keys nudge window position by 20px (auto-saved)
- **Enhanced:** Move-to submenu with 5 predefined positions (corners + center)

### 6. Pet reacts to mouse hover
- **DONE** — `enterEvent` triggers waving animation, `leaveEvent` returns to phase animation
- Uses existing `_play_once` / `_set_animation` / `_pick_animation`

### 7. Session history view
- Show last 10 sessions in a small popup
- Date, duration, pet used
- **Tech:** New `QDialog` or tooltip widget

### 8. Multiple pet support
- Allow spawning multiple pets simultaneously
- Each pet has its own timer or shares one
- **Tech:** List of `PetWindow` instances, shared timer state

### 8b. Right-click context menu
- **DONE** — Right-click on pet window shows pause/reset/skip/quit menu
- Styled dark glass menu matching the app aesthetic

### 8c. Long break support
- **DONE** — Every 4th session triggers a 15-minute long break
- Configurable via `long_break_interval` and `long_break_minutes` in config
- Purple color in UI, dedicated messages

### 8d. Skip phase
- **DONE** — `timer.skip_phase()` + `Cmd+Shift+S` shortcut
- Available via right-click context menu

### 9. Sound volume control
- **DONE** — `--volume 0-100` flag
- Saves to config: `pomo-pet config volume 50`
- Uses `afplay -v <vol/100>` for volume-scaled playback

### 10. Custom message support
- **DONE** — `--messages-file path/to/messages.txt`
- One message per line, random selection
- Saves to config: `pomo-pet config messages_file ~/msgs.txt`
- **Enhanced:** More messages (8 work, 3 break, 3 long break), time-of-day greetings (☀️/💪/🌆)

---

## 🟢 P2 — Nice to Have (backlog)

### 11. Statistics dashboard (GUI)
- Window showing charts: sessions per day, focus time trends
- Weekly/monthly views
- **Tech:** `QtCharts` or matplotlib embedded widget

### 12. Pet leveling system
- XP earned per session (1 XP per minute focused)
- Level up animations
- Unlock new animations at certain levels
- **Tech:** Extend `SessionStats` with XP/level fields

### 13. Config file support
- **DONE** — `~/.pomo-pet/config.json` for persistent settings
- Default pet, work/break duration, volume, sound, custom messages file
- `pomo-pet config` to view, `pomo-pet config key value` to set
- CLI flags override and auto-save to config

### 14. Theme system
- Light mode / dark mode toggle
- Custom accent colors
- **Tech:** Multiple `Theme` classes, runtime switching

### 15. Break-time mini-games
- Simple games during breaks (stretch reminder, breathing exercise)
- **Tech:** New widget with countdown + instructions

### 16. Pomodoro technique variants
- **DONE** — `pomo-pet presets` to list, `pomo-pet apply <name>` to apply
- Presets: classic (25/5), 52-17, 90min, sprint (15/3), custom
- Each preset sets work/break/long_break/interval in one command

### 17. Focus mode integration
- macOS Focus mode detection
- Auto-start timer when Focus activates
- **Tech:** `subprocess` polling or macOS notifications API

### 18. Export statistics
- **DONE** — `pomo-pet stats --format json` or `--format csv`
- StatsStore.export_json() and export_csv() methods
- Works with pipe: `pomo-pet stats --format json | jq .`

### 19. Multi-language support
- Translate messages to other languages
- **Tech:** i18n with message catalogs

### 20. Pet breeding / collection
- Combine pets to create new ones
- Pet collection gallery
- **Tech:** Complex, needs design spec

---

## 🔵 P3 — Future Vision

### 20a. Web app / PWA
- **DONE** — Static installable PWA in `docs/`
- Includes animated pets, work/break/long-break timer, local-first stats, notification permission flow, install manifest, service worker, offline app shell, and responsive desktop/mobile layout
- **Enhanced:** Hash-routed web workspace with Focus, Tasks, Pets, Stats, and Settings pages
- **Enhanced:** Built-in local task list; adding/selecting a task updates the current focus intention, and completed sessions credit minutes back to the active task
- **Enhanced:** Pet gallery panel with safe external discovery link to Codex Pets, custom spritesheet URL support, Codex Pets `/pets/{slug}`, `/share/{slug}`, API URL, and direct spritesheet imports
- **Fixed:** Web sprite rendering now uses pet metadata frame dimensions instead of hardcoded row offsets
- **Fixed:** Resting web pets use a still frame so sprites do not slide distractingly while idle
- **Enhanced:** Bundled Avocado, Mint, Blueberry, and Sunrise pet variants using the existing safe spritesheet asset
- **Enhanced:** Pet bond system with XP, levels, mood, daily focus goal, and goal progress ring
- **Enhanced:** Local insight cards for best recent day, average energy, and week-over-week momentum
- **Enhanced:** Focus intention input, quick intention chips, session history task labels, and local milestone achievements
- **Enhanced:** Restorative break prompts that rotate manually or when a work session completes
- **Enhanced:** Post-session reflection capture with local notes, energy rating, history display, import/export support, and share summary energy
- **Enhanced:** Local JSON stats import, JSON export, and share/copy focus summary
- **Enhanced:** First-run setup overlay and PWA readiness indicators for install, offline, and storage status
- **Enhanced:** Launch/share metadata, canonical tags, social preview tags, and SoftwareApplication structured data
- **Enhanced:** Generated 1200x630 launch preview image wired into Open Graph, Twitter cards, and manifest screenshots
- **Enhanced:** Browser title timer sync and optional screen wake-lock support while sessions run
- **Testing:** pytest PWA file checks, static PWA/repo-safety audit, Playwright E2E workflow in GitHub Actions, and task-list browser coverage
- **Next:** richer stats charts, task filters, and more bundled pet packs

### 21. Team mode
- Shared timer across team members
- See who's focusing, who's on break
- **Tech:** WebSocket server, client sync

### 22. Spotify integration
- Play focus music during work sessions
- Play relaxing music during breaks
- **Tech:** Spotify API, OAuth flow

### 23. AI-powered messages
- Use LLM to generate contextual motivational messages
- Based on time of day, session count, streak
- **Tech:** OpenAI API or local model

### 24. Voice commands
- "Hey pet, start timer"
- "Hey pet, pause"
- **Tech:** macOS Speech framework or Whisper

### 25. Widget support (macOS)
- macOS desktop widget showing timer
- **Tech:** WidgetKit, Swift bridge

### 26. Cross-platform builds
- Windows installer (`.exe`)
- Linux AppImage / Snap
- **Tech:** PyInstaller, briefcase
