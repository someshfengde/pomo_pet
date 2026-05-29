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

### 3. Pet sprite rendering quality
- `smoothscale` can produce blurry output on retina displays
- **Fix:** Load at 2x resolution, use `Qt.KeepAspectRatioByExpanding`, let Qt handle retina scaling

---

## 🟡 P1 — High Priority (next sprint)

### 4. Menu bar integration (macOS)
- **DONE** — `QSystemTrayIcon` with Pause/Reset/Quit menu
- Tooltip shows timer + phase
- Fixed in `src/ui/tray.py`

### 5. Global keyboard shortcuts
- **DONE** — `Cmd+Shift+P` pause, `Cmd+Shift+R` reset, `Cmd+Shift+Q` quit
- Uses `QShortcut` with `QKeySequence("Ctrl+Shift+…")` (maps to Cmd on macOS)

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
- 52/17 rule (52min work, 17min break)
- 90-minute deep work blocks
- **Tech:** Preset configurations in CLI

### 17. Focus mode integration
- macOS Focus mode detection
- Auto-start timer when Focus activates
- **Tech:** `subprocess` polling or macOS notifications API

### 18. Export statistics
- `pomo-pet --export stats.csv` for data export
- JSON/CSV formats
- **Tech:** Extend `StatsStore` with export methods

### 19. Multi-language support
- Translate messages to other languages
- **Tech:** i18n with message catalogs

### 20. Pet breeding / collection
- Combine pets to create new ones
- Pet collection gallery
- **Tech:** Complex, needs design spec

---

## 🔵 P3 — Future Vision

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
