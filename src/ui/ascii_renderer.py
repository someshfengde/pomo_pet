"""ASCII animation renderer — renders pet sprites as ASCII art in the terminal.

Similar to how OpenAI Codex renders their pet animations inline.
"""

import os
import shutil
import sys
import time
from pathlib import Path
from typing import List, Optional

from PIL import Image


# ASCII grayscale ramp (dark to light)
RAMP = " .:-=+*#%@"

def _pixel_to_char(r: int, g: int, b: int, a: int) -> str:
    """Convert RGBA pixel to ASCII character."""
    if a < 30:
        return " "
    brightness = (r + g + b) / 3
    idx = int(brightness / 255 * (len(RAMP) - 1))
    return RAMP[idx]


def _image_to_ascii(img: Image.Image, width: int = 40) -> str:
    """Convert a PIL Image to ASCII art string."""
    aspect = img.height / img.width
    height = int(width * aspect * 0.5)
    
    img = img.resize((width, height), Image.NEAREST)
    img = img.convert("RGBA")
    
    lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            r, g, b, a = img.getpixel((x, y))
            line += _pixel_to_char(r, g, b, a)
        lines.append(line)
    
    return "\n".join(lines)


def calc_ascii_width(frame_width: int, frame_height: int, max_width: Optional[int] = None) -> int:
    """Calculate optimal ASCII width based on sprite dimensions and terminal size.
    
    Logic:
    - Base ratio: ~1 ASCII char per 3-4 pixels of sprite width
    - Clamp to terminal width (leave margin for timer text)
    - Minimum 20, maximum 80
    
    Args:
        frame_width: Width of sprite frame in pixels.
        frame_height: Height of sprite frame in pixels.
        max_width: Override max width. If None, uses terminal width.
    
    Returns:
        Optimal ASCII width in characters.
    """
    # Base: ~1 char per 3.5 pixels (empirically good for readability)
    base_width = int(frame_width / 3.5)
    
    # Clamp to reasonable range
    base_width = max(20, min(base_width, 80))
    
    # Don't exceed terminal width (leave 10 chars margin for safety)
    if max_width is None:
        try:
            term_size = shutil.get_terminal_size((80, 24))
            max_width = term_size.columns - 10
        except Exception:
            max_width = 70
    
    return min(base_width, max_width)


def load_ascii_frames(spritesheet_path: str, frame_width: int, frame_height: int,
                       row: int, num_frames: int, display_width: Optional[int] = None) -> List[str]:
    """Load frames from spritesheet and convert to ASCII art.
    
    If display_width is None, automatically calculates optimal width
    based on sprite dimensions and terminal size.
    
    Args:
        spritesheet_path: Path to the spritesheet image.
        frame_width: Width of each frame in the spritesheet.
        frame_height: Height of each frame in the spritesheet.
        row: Which row of the spritesheet to use.
        num_frames: Number of frames to extract.
        display_width: Width of ASCII output in characters. None = auto.
    
    Returns:
        List of ASCII art strings, one per frame.
    """
    path = Path(spritesheet_path)
    if not path.exists():
        return []
    
    if display_width is None:
        display_width = calc_ascii_width(frame_width, frame_height)
    
    sheet = Image.open(path).convert("RGBA")
    frames = []
    
    for col in range(num_frames):
        x = col * frame_width
        y = row * frame_height
        frame = sheet.crop((x, y, x + frame_width, y + frame_height))
        ascii_art = _image_to_ascii(frame, width=display_width)
        frames.append(ascii_art)
    
    return frames


class AsciiAnimator:
    """Renders ASCII animation frames in the terminal."""
    
    def __init__(self, frames: List[str], fps: int = 8, loop: bool = True):
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self._start_time = time.time()
    
    def current_frame(self) -> str:
        """Get the current frame based on elapsed time."""
        if not self.frames:
            return ""
        
        elapsed = time.time() - self._start_time
        interval = 1.0 / self.fps
        idx = int(elapsed / interval)
        
        if self.loop:
            idx = idx % len(self.frames)
        else:
            idx = min(idx, len(self.frames) - 1)
        
        return self.frames[idx]
    
    def reset(self):
        """Reset animation to start."""
        self._start_time = time.time()


def clear_lines(n: int):
    """Clear n lines in the terminal."""
    for _ in range(n):
        sys.stdout.write("\033[2K")
        sys.stdout.write("\033[1A")
    sys.stdout.write("\033[2K")


def render_frame(frame: str):
    """Render a single frame to the terminal."""
    sys.stdout.write(frame)
    sys.stdout.flush()
