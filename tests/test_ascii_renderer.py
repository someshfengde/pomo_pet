"""Tests for ASCII animation renderer."""

import pytest
from src.ui.ascii_renderer import (
    _pixel_to_char,
    _image_to_ascii,
    load_ascii_frames,
    AsciiAnimator,
)


class TestPixelToChar:
    def test_black_pixel(self):
        char = _pixel_to_char(0, 0, 0, 255)
        # Black = darkest = "@" (end of ramp)
        assert char == " "  # brightness 0 maps to start of ramp

    def test_white_pixel(self):
        char = _pixel_to_char(255, 255, 255, 255)
        # White = brightest = "@" (end of ramp in our reversed ramp)
        assert char == "@"

    def test_transparent_pixel(self):
        char = _pixel_to_char(255, 255, 255, 0)
        assert char == " "

    def test_semi_transparent(self):
        char = _pixel_to_char(128, 128, 128, 100)
        assert isinstance(char, str)
        assert len(char) == 1


class TestImageToAscii:
    def test_converts_image(self):
        from PIL import Image
        img = Image.new("RGBA", (64, 64), (200, 200, 200, 255))
        ascii_art = _image_to_ascii(img, width=20)
        assert isinstance(ascii_art, str)
        assert len(ascii_art) > 0
        assert "\n" in ascii_art

    def test_width_parameter(self):
        from PIL import Image
        img = Image.new("RGBA", (64, 64), (200, 200, 200, 255))
        ascii_art = _image_to_ascii(img, width=10)
        lines = ascii_art.split("\n")
        assert all(len(line) <= 10 for line in lines if line)


class TestLoadAsciiFrames:
    def test_loads_from_spritesheet(self, tmp_path):
        from PIL import Image
        img = Image.new("RGBA", (192 * 6, 192), (100, 200, 100, 255))
        path = tmp_path / "spritesheet.webp"
        img.save(path, "WEBP")

        frames = load_ascii_frames(str(path), 192, 192, row=0, num_frames=6, display_width=20)
        assert len(frames) == 6
        assert all(isinstance(f, str) for f in frames)

    def test_missing_file(self):
        frames = load_ascii_frames("/nonexistent.webp", 192, 192, row=0, num_frames=6)
        assert frames == []


class TestAsciiAnimator:
    def test_current_frame(self):
        frames = ["frame1", "frame2", "frame3"]
        anim = AsciiAnimator(frames, fps=10, loop=True)
        frame = anim.current_frame()
        assert frame in frames

    def test_loop(self):
        frames = ["a", "b"]
        anim = AsciiAnimator(frames, fps=1000, loop=True)
        import time
        time.sleep(0.002)
        frame = anim.current_frame()
        assert frame in frames

    def test_no_loop_stops_at_last(self):
        frames = ["a", "b", "c"]
        anim = AsciiAnimator(frames, fps=1000, loop=False)
        import time
        time.sleep(0.01)
        frame = anim.current_frame()
        assert frame == "c"

    def test_reset(self):
        frames = ["a", "b"]
        anim = AsciiAnimator(frames, fps=1, loop=True)
        import time
        time.sleep(1.1)
        anim.reset()
        frame = anim.current_frame()
        assert frame == "a"

    def test_empty_frames(self):
        anim = AsciiAnimator([], fps=8)
        assert anim.current_frame() == ""
