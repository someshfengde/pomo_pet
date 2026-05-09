"""Load pet data from pet directories."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional


class PetLoadError(Exception):
    """Raised when a pet cannot be loaded."""


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


def load_pet(pet_dir: Path) -> Pet:
    """Load a pet from a directory containing pet.json and spritesheet.

    Args:
        pet_dir: Path to the pet directory.

    Returns:
        Pet object with loaded data.

    Raises:
        PetLoadError: If pet.json is missing, invalid, or spritesheet not found.
    """
    pet_dir = Path(pet_dir)
    json_path = pet_dir / "pet.json"

    if not json_path.exists():
        raise PetLoadError(f"pet.json not found in {pet_dir}")

    try:
        data = json.loads(json_path.read_text())
    except json.JSONDecodeError as e:
        raise PetLoadError(f"Invalid JSON in {json_path}: {e}") from e

    required_fields = ["id", "displayName", "description", "spritesheetPath", "kind"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise PetLoadError(f"Missing required fields in pet.json: {missing}")

    spritesheet = pet_dir / data["spritesheetPath"]
    if not spritesheet.exists():
        raise PetLoadError(f"Spritesheet not found: {spritesheet}")

    # Parse animations if present
    animations: Dict[str, AnimationDef] = {}
    for name, anim_data in data.get("animations", {}).items():
        animations[name] = AnimationDef(
            row=anim_data["row"],
            frames=anim_data["frames"],
            fps=anim_data["fps"],
            loop=anim_data.get("loop", True),
        )

    return Pet(
        id=data["id"],
        display_name=data["displayName"],
        description=data["description"],
        spritesheet_path=data["spritesheetPath"],
        kind=data["kind"],
        frame_width=data.get("frameWidth", 64),
        frame_height=data.get("frameHeight", 64),
        animations=animations,
    )


def list_pets(pets_root: Path) -> List[Pet]:
    """Discover all valid pets under a root directory.

    Args:
        pets_root: Path to the pets/ directory.

    Returns:
        List of Pet objects for all valid pet directories.
    """
    pets_root = Path(pets_root)
    pets: List[Pet] = []

    if not pets_root.is_dir():
        return pets

    for entry in sorted(pets_root.iterdir()):
        if not entry.is_dir():
            continue
        try:
            pets.append(load_pet(entry))
        except PetLoadError:
            continue

    return pets
