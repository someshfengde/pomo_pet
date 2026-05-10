"""Persistent configuration stored at ~/.pomo-pet/config.json."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".pomo-pet"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Config:
    """User preferences that persist across sessions."""
    default_pet: str = "avocado"
    work_minutes: int = 25
    break_minutes: int = 5
    volume: int = 80  # 0-100
    sound_enabled: bool = True
    messages_file: Optional[str] = None  # custom messages file path

    @classmethod
    def load(cls) -> "Config":
        """Load config from disk, or return defaults if not found."""
        if not CONFIG_FILE.exists():
            return cls()
        try:
            data = json.loads(CONFIG_FILE.read_text())
            # Only accept known fields
            known = {f.name for f in cls.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in known}
            return cls(**filtered)
        except (json.JSONDecodeError, TypeError, KeyError):
            return cls()

    def save(self) -> None:
        """Persist config to disk."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2) + "\n")

    def update(self, **kwargs) -> None:
        """Update fields and save."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
