"""Persistent configuration stored at ~/.pomo-pet/config.json."""

import json
from dataclasses import dataclass, asdict, replace
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
    long_break_minutes: int = 15
    long_break_interval: int = 4  # every N sessions triggers a long break (0 to disable)
    volume: int = 80  # 0-100
    sound_enabled: bool = True
    messages_file: Optional[str] = None  # custom messages file path
    window_x: Optional[int] = None  # saved window position X
    window_y: Optional[int] = None  # saved window position Y

    @classmethod
    def load(cls) -> "Config":
        """Load config from disk, or return defaults if not found."""
        if not CONFIG_FILE.exists():
            return cls()
        try:
            data = json.loads(CONFIG_FILE.read_text())
            if not isinstance(data, dict):
                return cls()
            # Only accept known fields
            known = {f.name for f in cls.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in known}
            config = cls()
            for key, value in filtered.items():
                try:
                    candidate = replace(config, **{key: value})
                    candidate.validate()
                    config = candidate
                except ValueError:
                    continue
            return config
        except (OSError, json.JSONDecodeError, TypeError, KeyError):
            return cls()

    def save(self) -> None:
        """Persist config to disk."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.validate()
        from pomo_pet.core.persistence import atomic_write
        atomic_write(CONFIG_FILE, json.dumps(asdict(self), indent=2) + "\n")

    def update(self, **kwargs) -> None:
        """Update fields and save."""
        updates = {key: value for key, value in kwargs.items() if key in self.__dataclass_fields__}
        candidate = replace(self, **updates)
        candidate.validate()
        candidate.save()
        self.__dict__.update(candidate.__dict__)

    def validate(self) -> None:
        limits = {"work_minutes": (1, 180), "break_minutes": (1, 90),
                  "long_break_minutes": (0, 120), "long_break_interval": (0, 12),
                  "volume": (0, 100)}
        for key, (minimum, maximum) in limits.items():
            value = getattr(self, key)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")
        if type(self.sound_enabled) is not bool:
            raise ValueError("sound_enabled must be true or false")
        if not isinstance(self.default_pet, str) or not self.default_pet.strip():
            raise ValueError("default_pet must be a nonempty name")
        if self.messages_file is not None and not isinstance(self.messages_file, str):
            raise ValueError("messages_file must be a path or none")
        for key in ("window_x", "window_y"):
            if getattr(self, key) is not None and type(getattr(self, key)) is not int:
                raise ValueError(f"{key} must be an integer or none")
