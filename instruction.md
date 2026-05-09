## Core Idea

Pomo Pet is a CLI application that combines the Pomodoro productivity technique with cute, interactive digital pets. Users can spawn their favorite pet on screen and watch it count down their work and break sessions while they focus on their tasks.

## Project Overview

**Pomo Pet** is a Python-based CLI tool that:
- Displays an animated pet on the user's screen that can be moved freely
- Runs a customizable Pomodoro timer (default: 25 min work, 5 min break)
- Shows a status bar with the timer in the top right corner
- Enables the pet to provide motivational feedback during work and rest sessions
- Allows community contributions of new pets via pull requests

## Features

### Core Features
1. **Pet Spawning & Display**
   - Spawn pets with animated spritesheets (WebP format)
   - Display pets as interactive windows on screen
   - Support for dragging/moving pets anywhere on screen

2. **Pomodoro Timer**
   - Standard 25-minute work session / 5-minute break cycle
   - Customizable timer durations (configurable via CLI)
   - Visual countdown in the pet's status bar (top right)
   - Timer display format: MM:SS

3. **Pet Interactions & Messages**
   - Pet reacts to timer phases:
     - During work: Encouraging messages ("Focus time!", "You've got this!")
     - During break: Rest reminders ("Take a break!", "Rest your eyes!")
     - At completion: Celebration messages ("Great session!", "You crushed it!")
   - Extensible messaging system for custom pet personalities

4. **Customization**
   - CLI options to set work duration and break duration
   - Support for multiple pets (selected at startup)
   - Pet selection menu with preview of available pets

### Optional Enhanced Features (Sky's the Limit!)
- Pet idle animations and reactions
- Sound notifications (optional) for timer events
- Statistics tracking (sessions completed, total focus time)
- Pet leveling/progression system
- Multiple pets visible simultaneously
- Dark mode / light mode themes
- Desktop notifications

## Project Structure ( Rough feel free to modify as needed)

```
pomo_pet/
├── instruction.md              # This file - project guidelines
├── pets/                       # Directory containing all available pets
│   └── avocado/
│       ├── pet.json           # Pet metadata and configuration
│       └── spritesheet.webp   # Pet animation spritesheet
├── src/
│   ├── cli.py                 # CLI entry point and argument parsing
│   ├── pet_renderer.py        # Display and rendering logic
│   ├── timer.py               # Pomodoro timer logic and state
│   ├── pet_loader.py          # Load pet data from JSON
│   └── messages.py            # Pet dialog/message system
├── tests/
│   ├── test_timer.py          # Timer functionality tests
│   ├── test_pet_loader.py     # Pet loading tests
│   ├── test_messages.py       # Message system tests
│   └── test_integration.py    # End-to-end integration tests
├── pyproject.toml            # Python dependencies
|-- uv.lock
└── README.md                   # User-facing documentation
```

## Setup & Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation Steps
1. Clone the repository
2. Navigate to the project directory: `cd pomo_pet`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python -m src.cli`

### Dependencies (To Include in requirements.txt)
- `click` - CLI argument parsing
- `pillow` - Image handling for spritesheets
- `pygame` or similar - Window management and rendering (pending selection)
- `pytest` - Testing framework
- `pytest-cov` - Test coverage reporting

## Usage

### Basic Usage
```bash
python -m src.cli --pet avocado
```

### With Custom Timer Settings
```bash
python -m src.cli --pet avocado --work 25 --break 5
```

### Available Options
- `--pet <name>` - Select which pet to display (e.g., avocado)
- `--work <minutes>` - Set work session duration (default: 25)
- `--break <minutes>` - Set break session duration (default: 5)
- `--list-pets` - Display all available pets
- `--help` - Show help message

## Adding New Pets (Contributing)

### For Contributors: Submitting a New Pet

1. **Create a Pet Directory**
   - Create a new folder under `pets/` with your pet's name (lowercase, no spaces)
   - Example: `pets/dragon/`

2. **Create pet.json**
   ```json
   {
     "id": "dragon",
     "displayName": "Dragon",
     "description": "A majestic dragon pet with fire breathing animations.",
     "spritesheetPath": "spritesheet.webp",
     "kind": "creature"
   }
   ```
   - `id`: Unique identifier (lowercase, used in CLI)
   - `displayName`: Human-friendly name
   - `description`: Short description of the pet
   - `spritesheetPath`: Path to spritesheet file (relative to pet directory)
   - `kind`: Type of pet (e.g., "creature", "animal", "fantasy")

3. **Prepare Spritesheet**
   - Create an animated spritesheet in WebP format
   - Dimensions: TBD (to be specified in developer docs)
   - Include frames for: idle, happy, tired, celebrating states
   - Recommended tool: [Aseprite](https://www.aseprite.org/) or free alternatives

4. **Submit a Pull Request**
   - Fork the repository
   - Add your pet directory to `pets/`
   - Include your pet's spritesheet
   - Write a brief description in your PR message
   - Reference Codex Pets if inspired by that website

### Pet Data Source
- **Codex Pets**: https://codex-pets.net/ (reference/inspiration, not required)
- You can create original pets or adapt existing ones with proper attribution

## Development Guidelines

### Code Quality
- Write clean, documented Python code
- Follow PEP 8 style guidelines
- Use type hints for function parameters and returns
- Add docstrings to all functions and classes

### Testing Requirements
- All new features must include unit tests
- Aim for at least 80% code coverage
- Run tests before submitting PRs: `pytest`
- Run coverage report: `pytest --cov=src`

### Testing Checklist
- [ ] Timer starts and counts down correctly
- [ ] Pet displays and can be moved
- [ ] Pet messages change based on timer phase
- [ ] Timer transitions from work to break correctly
- [ ] Custom timer durations work as expected
- [ ] Multiple pets can be loaded without errors
- [ ] Application runs cleanly without warnings

### Before Committing
- Run `pytest` to ensure all tests pass
- Run `pytest --cov=src` to check coverage
- Test the CLI manually with different pets and timer settings
- Verify no errors in console output

## Implementation Phases

### Phase 1: Core CLI & Timer ✓
- [ ] CLI argument parsing with Click
- [ ] Pomodoro timer logic with configurable durations
- [ ] Basic pet loading from JSON

### Phase 2: Pet Display & Rendering
- [ ] Window management (create/show pet window)
- [ ] Load and display pet spritesheets
- [ ] Pet dragging/movement on screen

### Phase 3: Integration & Messaging
- [ ] Connect timer to pet display
- [ ] Implement pet message system
- [ ] Timer phase transitions with visual/message feedback

### Phase 4: Polish & Testing
- [ ] Comprehensive test suite
- [ ] Error handling and user feedback
- [ ] Documentation and examples

### Phase 5: Optional Enhancements
- [ ] Statistics tracking
- [ ] Sound notifications
- [ ] Pet animations and idle states
- [ ] UI improvements and themes

## Testing Strategy

### Unit Tests
- `test_timer.py`: Test timer logic, phase transitions, custom durations
- `test_pet_loader.py`: Test loading pets from JSON, error handling
- `test_messages.py`: Test message selection based on timer state

### Integration Tests
- `test_integration.py`: End-to-end tests with full CLI workflow

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_timer.py

# Run with coverage
pytest --cov=src --cov-report=html
```

## Common Issues & Troubleshooting

- **Pet not displaying**: Check spritesheet path in pet.json
- **Timer not updating**: Verify timer logic and refresh rate
- **CLI crashes**: Check Python version (3.8+) and dependencies installed
- **Can't move pet**: Ensure window manager is compatible with OS

## Contributing Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/pet-name`)
3. Implement your changes with tests
4. Ensure all tests pass: `pytest`
5. Submit a pull request with a clear description

## License & Attribution

- Codex Pets reference: https://codex-pets.net/
- Please credit original pet creators if adapting existing designs
- Maintain the open-source spirit of contributions

## Contact & Support

For questions or issues, please open a GitHub issue or discussion. 

