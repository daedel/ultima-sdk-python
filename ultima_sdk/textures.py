"""
Textures module - Manages landscape texture data.

Textures (texmaps.mul) are square 16-bit BGR555 images, either 64x64 or
128x128.  Pixel values are raw 16-bit ushorts; no opacity bit is used
(textures are always fully opaque in the renderer).

Verdata patching is handled externally via Verdata.apply() at startup.
"""
from pathlib import Path
from typing import Optional

from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException, FileParseError

import struct

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

        Textures are stored as raw 16-bit BGR555 (2 bytes per pixel).
        """
        return image_from_pixels(self.width, self.height, self.pixels)


class Textures:
    """Static class for managing texture data."""

    _index: Optional[FileIndex] = None
    _initialized = False

    # Verdata patch cache: texture_id -> raw bytes
    _patch_cache: dict = {}

    @classmethod
    def initialize(
        cls,
        idx_path: str | None = None,
        mul_path: str | None = None
    ) -> bool:
        """Initialize texture index."""
        if cls._initialized:
            return True
        try:
            if idx_path is None:
                idx_path = Files.get_file_path("texidx.mul")
            if mul_path is None:
                mul_path = Files.get_file_path("texmaps.mul")
            if idx_path and mul_path:
                cls._index = FileIndex(idx_path, mul_path)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize textures: {e}")
        return False

    @classmethod
    def get_texture(cls, texture_id: int) -> Optional["TextureData"]:
        """Get texture by ID."""
        if not cls._initialized:
            cls.initialize()

        # Check verdata patch cache first.
        if texture_id in cls._patch_cache:
            raw = cls._patch_cache[texture_id]
        else:
            if not cls._index:
                return None
            raw = cls._index.read_raw(texture_id)
            if not raw:
                return None

        width, height, pixels = cls._decode_texture(raw)
        return TextureData(
            texture_id=texture_id,
            width=width,
            height=height,
            pixels=pixels
        )

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

    @classmethod
    def apply_verdata_patch(cls, block_id: int, data: bytes) -> None:
        """Cache raw verdata patch bytes for a texture.

        Subsequent calls to get_texture(block_id) will decode from these
        bytes instead of reading from texmaps.mul.
        """
        if not cls._initialized:
            cls.initialize()
        cls._patch_cache[block_id] = data

    @staticmethod
    def _decode_texture(data: bytes) -> tuple[int, int, bytes]:
        """Decode a texture entry from texmaps.mul.

        Client files store textures as raw 16-bit pixels with a fixed square
        size; the two supported sizes are 64x64 and 128x128.

        Fallback fixture layout: uint16 width, uint16 height, then pixels.
        """
        # Fixed-size real client formats.
        if len(data) == 64 * 64 * 2:
            return 64, 64, data
        if len(data) == 128 * 128 * 2:
            return 128, 128, data

        # Fixture format: 4-byte header + pixels.
        if len(data) >= 4:
            w, h = struct.unpack_from("<HH", data, 0)
            if w > 0 and h > 0:
                expected = 4 + (w * h * 2)
                if len(data) == expected:
                    return w, h, data[4:]

        raise FileParseError("Unsupported texture data format")
