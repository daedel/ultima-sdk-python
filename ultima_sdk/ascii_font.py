"""ASCII font reader for fonts.mul.

Decodes all 10 UO ASCII font sets from fonts.mul into per-character
Pillow RGBA images.  Ported from NerdyGamers/UOPython with adaptations
to match UltimaWorks SDK conventions (Files lookup, BinaryReader,
no auto-execute on import).
"""

from __future__ import annotations

from typing import IO

from PIL import Image

from ultima_sdk.files import Files
from ultima_sdk.rendering import uo16_to_rgba


def _read_byte(f: IO[bytes]) -> int:
    return f.read(1)[0]


class AsciiFont:
    """A single ASCII font face decoded from fonts.mul.

    Parameters
    ----------
    index:
        Zero-based font index (0-9).
    """

    FONTS: list["AsciiFont"] = []

    def __init__(self, index: int, header: int) -> None:
        self.index = index
        self.header = header
        self.height: int = 0
        self._characters: dict[str, Image.Image] = {}

    # ------------------------------------------------------------------
    # class-level loader
    # ------------------------------------------------------------------

    @classmethod
    def load(cls) -> None:
        """Read fonts.mul and populate ``AsciiFont.FONTS``.

        Safe to call multiple times; clears previous state.
        """
        cls.FONTS.clear()
        path = Files.get_file_path("fonts.mul")
        with open(path, "rb") as f:
            for font_idx in range(10):
                header = _read_byte(f)
                font = cls(font_idx, header)
                cls.FONTS.append(font)

                for char_offset in range(224):
                    width = _read_byte(f)
                    height = _read_byte(f)
                    _read_byte(f)  # unknown padding byte

                    # Only characters in the first 96 slots influence font.height
                    if char_offset < 96:
                        font.height = max(font.height, height)

                    img = Image.new(
                        "RGBA", (max(width, 1), max(height, 1)), (0, 0, 0, 0)
                    )
                    if width > 0 and height > 0:
                        pos = f.tell()
                        stride = 2 * width
                        for y in range(height):
                            f.seek(pos)
                            pos += stride
                            for x in range(width):
                                lo = _read_byte(f)
                                hi = _read_byte(f)
                                pixel = lo | (hi << 8)
                                if pixel > 0:
                                    rgba = uo16_to_rgba(pixel ^ 0x8000)
                                    img.putpixel((x, y), rgba)

                    char = chr(char_offset + 32)
                    font._characters[char] = img

    # ------------------------------------------------------------------
    # instance helpers
    # ------------------------------------------------------------------

    def get_character(self, letter: str) -> Image.Image:
        return self._characters[letter]

    def character_images(self, text: str) -> list[Image.Image]:
        return [self._characters[c] for c in text if c in self._characters]

    def get_width(self, text: str) -> int:
        return sum(img.width for img in self.character_images(text)) + 2

    def render_string(self, text: str) -> Image.Image:
        """Render *text* into a single RGBA image."""
        imgs = self.character_images(text)
        width = sum(img.width for img in imgs) + 2
        height = self.height + 2
        canvas = Image.new("RGBA", (max(width, 1), max(height, 1)), (0, 0, 0, 0))
        x = 2
        for img in imgs:
            canvas.paste(img, (x, height - img.height))
            x += img.width
        return canvas

    # ------------------------------------------------------------------
    # class-level convenience
    # ------------------------------------------------------------------

    @classmethod
    def get(cls, index: int) -> "AsciiFont":
        """Return the font at *index*, loading all fonts if needed."""
        if not cls.FONTS:
            cls.load()
        return cls.FONTS[index]
