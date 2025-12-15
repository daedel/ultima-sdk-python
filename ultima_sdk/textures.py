"""
Textures module - Manages landscape texture data.
"""

from pathlib import Path
from typing import Optional
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException

import struct

from .exceptions import FileParseError
from .rendering import image_from_pixels


class TextureData:
    """Represents a texture."""

    def __init__(self, texture_id: int, width: int, height: int, pixels: bytes):
        self.texture_id = texture_id
        self.width = width
        self.height = height
        self.pixels = pixels

    def to_image(self):
        """Convert this texture's pixels to a Pillow image.

        Textures are typically stored as 16-bit 5-5-5 (2 bytes per pixel).
        """
        return image_from_pixels(self.width, self.height, self.pixels)


class Textures:
    """Static class for managing texture data."""

    _index: Optional[FileIndex] = None
    _initialized = False

    @classmethod
    def initialize(cls, idx_path: str | None = None, mul_path: str | None = None) -> bool:
        """Initialize texture index."""
        if cls._initialized:
            return True

        try:
            if idx_path is None:
                idx_path = Files.get_file_path("texidx.mul")
            if mul_path is None:
                mul_path = Files.get_file_path("texmaps.mul")

            if idx_path and mul_path:
                from .file_index import FileIndex
                from .verdata_ids import IDS as VERDATA_IDS

                cls._index = FileIndex(idx_path, mul_path, file_id=VERDATA_IDS.TEXMAPS_MUL)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize textures: {e}")

        return False

    @classmethod
    def get_texture(cls, texture_id: int) -> Optional[TextureData]:
        """Get texture by ID."""
        if not cls._initialized:
            cls.initialize()

        if not cls._index:
            return None

        raw = cls._index.read_raw(texture_id)
        if not raw:
            return None

        width, height, pixels = cls._decode_texture(raw)
        return TextureData(texture_id=texture_id, width=width, height=height, pixels=pixels)

    @classmethod
    def save_png(cls, texture_id: int, path) -> bool:
        """Save a texture as a PNG.

        Returns True if the texture existed and was saved; False if missing.
        """
        try:
            out_path = Path(path)
        except Exception as e:
            raise FileAccessException(f"Invalid output path: {e}")

        tex = cls.get_texture(int(texture_id))
        if tex is None:
            return False

        try:
            img = tex.to_image()
            img.save(str(out_path), format="PNG")
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to save texture PNG: {e}")

    @staticmethod
    def _decode_texture(data: bytes) -> tuple[int, int, bytes]:
        """Decode a texture entry from texmaps.mul.

        Real client files typically store textures as raw 16-bit pixels with a
        fixed square size; common sizes are 64x64 and 128x128.

        Supported layouts:
        - Raw pixels only (preferred):
          - 64x64x2 bytes (8192)
          - 128x128x2 bytes (32768)
        - Fixture/debug layout: uint16 width, uint16 height, then pixels.
        """
        # Fixed-size real client formats.
        if len(data) == 64 * 64 * 2:
            return 64, 64, data
        if len(data) == 128 * 128 * 2:
            return 128, 128, data

        # Raw fixture format: <HH then width*height*2.
        if len(data) >= 4:
            w, h = struct.unpack_from("<HH", data, 0)
            if w > 0 and h > 0:
                expected = 4 + (w * h * 2)
                if len(data) == expected:
                    return w, h, data[4:]

        raise FileParseError("Unsupported texture data format")
