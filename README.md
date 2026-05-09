# Pomo Pet 🐾

A Pomodoro timer with cute digital pets! Combine productivity with adorable companions.

## Features

- **Animated pet display** - floating window with spritesheet animation
- **Draggable pet** - click and drag to move the pet anywhere on screen
- **Live timer** - countdown displayed in the pet's status bar
- **Phase-aware messages** - pet reacts to work and break sessions
- **Customizable** - set your own work/break durations
- **Multiple pets** - add your own via pull requests!

## Installation

```bash
git clone <repo-url>
cd pomo_pet
uv sync
uv pip install -e .
```

## Usage

### List available pets
```bash
pomo-pet --list-pets
```

### Start with a pet
```bash
pomo-pet --pet avocado
```

### Custom timer durations
```bash
pomo-pet --pet avocado --work 30 --break 10
```

### Window controls
- **Drag** the pet to move it around your screen
- **Q** or **ESC** to quit

### All options
```
Usage: pomo-pet [OPTIONS]

  Pomo Pet - A Pomodoro timer with cute digital pets!

Options:
  --pet TEXT       Pet to display (e.g., avocado)
  --work INTEGER   Work session duration in minutes (default: 25)
  --break INTEGER  Break session duration in minutes (default: 5)
  --list-pets      List all available pets
  --help           Show this message and exit.
```

## Adding New Pets

1. Create a directory under `pets/` with your pet's name (lowercase, no spaces)
2. Add a `pet.json`:
   ```json
   {
     "id": "dragon",
     "displayName": "Dragon",
     "description": "A majestic dragon pet.",
     "spritesheetPath": "spritesheet.webp",
     "kind": "creature"
   }
   ```
3. Add a `spritesheet.webp` with animated frames (64x64 per frame)
4. Submit a pull request!

## Development

### Run tests
```bash
uv run pytest tests/ -v
```

### Run with coverage
```bash
uv run pytest tests/ --cov=src --cov-report=term-missing
```

### Project structure
```
pomo_pet/
├── pets/                    # Pet definitions
│   └── avacado/
│       ├── pet.json         # Pet metadata
│       └── spritesheet.webp # Animation frames
├── src/
│   ├── __init__.py
│   ├── __main__.py          # python -m src entry point
│   ├── cli.py               # Click CLI + timer loop
│   ├── timer.py             # Pomodoro timer logic
│   ├── pet_loader.py        # Load pets from JSON
│   ├── pet_renderer.py      # Pillow spritesheet handling
│   ├── pet_window.py        # Pygame window + rendering
│   └── messages.py          # Pet message system
├── tests/
│   ├── test_timer.py
│   ├── test_pet_loader.py
│   ├── test_messages.py
│   ├── test_pet_renderer.py
│   ├── test_pet_window.py
│   ├── test_cli.py
│   └── test_integration.py
├── pyproject.toml
└── README.md
```

## Tech Stack

- **Python 3.13+**
- **Click** - CLI argument parsing
- **pygame-ce** - Window management and rendering
- **Pillow** - Image handling for spritesheets
- **pytest** - Testing framework
- **uv** - Package management

## License

MIT
