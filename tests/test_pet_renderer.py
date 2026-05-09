"""Tests for pet renderer (spritesheet loading and display logic)."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.pet_renderer import PetRenderer


class TestPetRendererInit:
    """Test renderer initialization."""

    def test_renderer_stores_pet(self):
        """Renderer keeps a reference to the pet."""
        pet = MagicMock()
        pet.display_name = "Avocado"
        renderer = PetRenderer(pet)
        assert renderer.pet is pet

    def test_renderer_default_size(self):
        """Renderer has a default display size."""
        pet = MagicMock()
        renderer = PetRenderer(pet)
        assert renderer.width > 0
        assert renderer.height > 0


class TestSpritesheetLoading:
    """Test spritesheet image loading."""

    def test_load_spritesheet_valid(self, tmp_path):
        """Loads a valid spritesheet image."""
        # Create a minimal valid image
        from PIL import Image

        img = Image.new("RGBA", (128, 128), (255, 255, 255, 255))
        spritesheet_path = tmp_path / "spritesheet.webp"
        img.save(spritesheet_path, "WEBP")

        pet = MagicMock()
        pet.spritesheet_path = str(spritesheet_path)

        renderer = PetRenderer(pet)
        assert renderer.spritesheet is not None

    def test_load_spritesheet_missing(self, tmp_path):
        """Handles missing spritesheet gracefully."""
        pet = MagicMock()
        pet.spritesheet_path = str(tmp_path / "nonexistent.webp")

        renderer = PetRenderer(pet)
        assert renderer.spritesheet is None


class TestSpriteExtraction:
    """Test extracting individual frames from spritesheet."""

    def test_extract_frames(self, tmp_path):
        """Extracts frames from a spritesheet grid."""
        from PIL import Image

        # Create a 256x128 spritesheet (2 columns, 1 row of 128x128 frames)
        img = Image.new("RGBA", (256, 128), (255, 0, 0, 255))
        spritesheet_path = tmp_path / "spritesheet.webp"
        img.save(spritesheet_path, "WEBP")

        pet = MagicMock()
        pet.spritesheet_path = str(spritesheet_path)

        renderer = PetRenderer(pet)
        frames = renderer.extract_frames(frame_width=128, frame_height=128)
        assert len(frames) == 2

    def test_extract_single_frame(self, tmp_path):
        """Extracts a single frame when spritesheet is one frame."""
        from PIL import Image

        img = Image.new("RGBA", (64, 64), (0, 255, 0, 255))
        spritesheet_path = tmp_path / "spritesheet.webp"
        img.save(spritesheet_path, "WEBP")

        pet = MagicMock()
        pet.spritesheet_path = str(spritesheet_path)

        renderer = PetRenderer(pet)
        frames = renderer.extract_frames(frame_width=64, frame_height=64)
        assert len(frames) == 1
