"""Pet display and rendering logic using Pillow."""

from pathlib import Path
from typing import List, Optional

from PIL import Image


class PetRenderer:
    """Handles loading and extracting frames from pet spritesheets."""

    def __init__(self, pet, width: int = 200, height: int = 200) -> None:
        self.pet = pet
        self.width = width
        self.height = height
        self.spritesheet: Optional[Image.Image] = None
        self._load_spritesheet()

    def _load_spritesheet(self) -> None:
        """Load the pet's spritesheet image."""
        path = Path(self.pet.spritesheet_path)
        if path.exists():
            self.spritesheet = Image.open(path)
        else:
            self.spritesheet = None

    def extract_frames(self, frame_width: int = 64, frame_height: int = 64) -> List[Image.Image]:
        """Extract individual frames from the spritesheet grid.

        Args:
            frame_width: Width of each frame in pixels.
            frame_height: Height of each frame in pixels.

        Returns:
            List of PIL Image objects, one per frame.
        """
        if self.spritesheet is None:
            return []

        sheet = self.spritesheet
        cols = sheet.width // frame_width
        rows = sheet.height // frame_height

        frames: List[Image.Image] = []
        for row in range(rows):
            for col in range(cols):
                x = col * frame_width
                y = row * frame_height
                frame = sheet.crop((x, y, x + frame_width, y + frame_height))
                frames.append(frame)

        return frames
