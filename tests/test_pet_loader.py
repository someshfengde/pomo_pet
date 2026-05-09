"""Tests for pet loading from JSON."""

import json
import pytest
from pathlib import Path
from src.pets.models import Pet, AnimationDef
from src.pets.loader import load_pet, list_pets, PetLoadError


class TestAnimationDef:
    def test_create(self):
        anim = AnimationDef(row=0, frames=6, fps=8, loop=True)
        assert anim.row == 0
        assert anim.frames == 6
        assert anim.fps == 8
        assert anim.loop is True


class TestPetDataClass:
    def test_pet_has_required_fields(self):
        pet = Pet(
            id="avocado",
            display_name="Avocado",
            description="A cute avocado pet.",
            spritesheet_path="spritesheet.webp",
            kind="creature",
        )
        assert pet.id == "avocado"
        assert pet.frame_width == 64
        assert pet.animations == {}

    def test_pet_with_animations(self):
        anims = {"idle": AnimationDef(row=0, frames=6, fps=8, loop=True)}
        pet = Pet(
            id="test",
            display_name="Test",
            description="Test",
            spritesheet_path="test.webp",
            kind="creature",
            frame_width=192,
            frame_height=192,
            animations=anims,
        )
        assert pet.frame_width == 192
        assert "idle" in pet.animations
        assert pet.animations["idle"].frames == 6


class TestLoadPet:
    def test_load_valid_pet(self, tmp_path):
        pet_dir = tmp_path / "avocado"
        pet_dir.mkdir()
        pet_data = {
            "id": "avocado",
            "displayName": "Avocado",
            "description": "A cute avocado pet.",
            "spritesheetPath": "spritesheet.webp",
            "kind": "creature",
        }
        (pet_dir / "pet.json").write_text(json.dumps(pet_data))
        (pet_dir / "spritesheet.webp").write_bytes(b"fake_image")

        pet = load_pet(pet_dir)
        assert pet.id == "avocado"
        assert pet.frame_width == 64  # default

    def test_load_pet_with_animations(self, tmp_path):
        pet_dir = tmp_path / "pet"
        pet_dir.mkdir()
        pet_data = {
            "id": "test",
            "displayName": "Test",
            "description": "Test pet.",
            "spritesheetPath": "spritesheet.webp",
            "kind": "creature",
            "frameWidth": 192,
            "frameHeight": 192,
            "animations": {
                "idle": {"row": 0, "frames": 6, "fps": 8, "loop": True},
                "running": {"row": 7, "frames": 6, "fps": 10, "loop": True},
            },
        }
        (pet_dir / "pet.json").write_text(json.dumps(pet_data))
        (pet_dir / "spritesheet.webp").write_bytes(b"fake")

        pet = load_pet(pet_dir)
        assert pet.frame_width == 192
        assert len(pet.animations) == 2
        assert pet.animations["idle"].row == 0
        assert pet.animations["running"].fps == 10

    def test_load_pet_missing_json(self, tmp_path):
        pet_dir = tmp_path / "no_pet"
        pet_dir.mkdir()
        with pytest.raises(PetLoadError, match="pet.json"):
            load_pet(pet_dir)

    def test_load_pet_missing_spritesheet(self, tmp_path):
        pet_dir = tmp_path / "bad_pet"
        pet_dir.mkdir()
        (pet_dir / "pet.json").write_text(json.dumps({
            "id": "bad", "displayName": "Bad", "description": "Bad.",
            "spritesheetPath": "spritesheet.webp", "kind": "creature",
        }))
        with pytest.raises(PetLoadError, match="spritesheet"):
            load_pet(pet_dir)

    def test_load_pet_invalid_json(self, tmp_path):
        pet_dir = tmp_path / "broken"
        pet_dir.mkdir()
        (pet_dir / "pet.json").write_text("not valid json {{{")
        with pytest.raises(PetLoadError):
            load_pet(pet_dir)

    def test_load_pet_missing_required_field(self, tmp_path):
        pet_dir = tmp_path / "incomplete"
        pet_dir.mkdir()
        (pet_dir / "pet.json").write_text(json.dumps({"id": "x"}))
        with pytest.raises(PetLoadError):
            load_pet(pet_dir)


class TestListPets:
    def test_list_pets_finds_all(self, tmp_path):
        for name in ["avocado", "dragon"]:
            pet_dir = tmp_path / name
            pet_dir.mkdir()
            (pet_dir / "pet.json").write_text(json.dumps({
                "id": name, "displayName": name.title(), "description": f"A {name} pet.",
                "spritesheetPath": "spritesheet.webp", "kind": "creature",
            }))
            (pet_dir / "spritesheet.webp").write_bytes(b"fake")

        pets = list_pets(tmp_path)
        assert len(pets) == 2

    def test_list_pets_skips_invalid(self, tmp_path):
        valid_dir = tmp_path / "avocado"
        valid_dir.mkdir()
        (valid_dir / "pet.json").write_text(json.dumps({
            "id": "avocado", "displayName": "Avocado", "description": "A pet.",
            "spritesheetPath": "spritesheet.webp", "kind": "creature",
        }))
        (valid_dir / "spritesheet.webp").write_bytes(b"fake")

        invalid_dir = tmp_path / "broken"
        invalid_dir.mkdir()
        (invalid_dir / "pet.json").write_text("bad json")

        pets = list_pets(tmp_path)
        assert len(pets) == 1

    def test_list_pets_empty_directory(self, tmp_path):
        assert list_pets(tmp_path) == []
