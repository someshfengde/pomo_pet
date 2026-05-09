"""Pet data models."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AnimationDef:
    """Definition of a single animation state."""
    row: int
    frames: int
    fps: int
    loop: bool


@dataclass
class Pet:
    """A pet with its metadata and spritesheet."""

    id: str
    display_name: str
    description: str
    spritesheet_path: str
    kind: str
    frame_width: int = 64
    frame_height: int = 64
    animations: Dict[str, AnimationDef] = field(default_factory=dict)
