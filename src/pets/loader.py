"""Load pet data from pet directories."""

import json
from pathlib import Path
from typing import List

from src.pets.models import Pet, AnimationDef


class PetLoadError(Exception):
    """Raised when a pet cannot be loaded."""


def load_pet(pet_dir: Path) -> Pet:
    """Load a pet from a directory containing pet.json and spritesheet."""
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

    animations = {}
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
        spritesheet_path=str(spritesheet.resolve()),
        kind=data["kind"],
        frame_width=data.get("frameWidth", 64),
        frame_height=data.get("frameHeight", 64),
        animations=animations,
    )


def list_pets(pets_root: Path) -> List[Pet]:
    """Discover all valid pets under a root directory."""
    pets_root = Path(pets_root)
    pets = []

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
