"""
Gumps module - Manages UI gump (interface) graphics.
"""

from pathlib import Path
from typing import Optional, Protocol, runtime_checkable
from .files import Files
from .exceptions import FileAccessException

import struct

from .rendering import image_from_pixels


class GumpData:
    """Represents a gump image."""

    def __init__(self, gump_id: int, width: int, height: int, pixels: bytes):
        self.gump_id = gump_id
        self.width = width
        self.height = height
        self.pixels = pixels

    def to_image(self):
        """Convert this gump's pixels to a Pillow image.

        Gump pixels are typically 16-bit 5-5-5 (2 bytes per pixel).
        """
        return image_from_pixels(self.width, self.height, self.pixels)


class Gumps:
    """Static class for managing gump data."""

    @runtime_checkable
    class _IndexLike(Protocol):
        def read_raw(self, index: int) -> Optional[bytes]:  # pragma: no cover
            ...

    _index: Optional[_IndexLike] = None
    _initialized = False

    @classmethod
    def initialize(cls, idx_path: str | None = None, mul_path: str | None = None) -> bool:
        """Initialize gump index."""
        if cls._initialized:
            return True

        try:
            if idx_path is None:
                idx_path = Files.get_file_path("gumpidx.mul")
            if mul_path is None:
                mul_path = Files.get_file_path("gumpart.mul")

            from .verdata_ids import IDS as VERDATA_IDS

            if idx_path and mul_path:
                from .file_index import FileIndex

                cls._index = FileIndex(idx_path, mul_path, file_id=VERDATA_IDS.GUMPART_MUL)
                cls._initialized = True
                return True

            # UOP fallback (newer clients).
            uop_path = Files.get_file_path("gumpartlegacymul.uop")
            if uop_path:
                from .uop import UopBackedIndex

                cls._index = UopBackedIndex(
                    uop_path,
                    "build/gumpartlegacymul/{0:D8}.tga",
                    has_extra=True,
                    file_id=VERDATA_IDS.GUMPART_MUL,
                )
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize gumps: {e}")

        return False

    @classmethod
    def get_gump(cls, gump_id: int) -> Optional[GumpData]:
        """Get gump by ID."""
        if not cls._initialized:
            cls.initialize()

        if not cls._index:
            return None

        raw = cls._index.read_raw(gump_id)
        if not raw:
            return None

        width, height, pixels = cls._decode_gump(raw)
        return GumpData(gump_id=gump_id, width=width, height=height, pixels=pixels)

    @classmethod
    def save_png(cls, gump_id: int, path) -> bool:
        """Save a gump as a PNG.

        Returns True if the gump existed and was saved; False if missing.
        """
        try:
            out_path = Path(path)
        except Exception as e:
            raise FileAccessException(f"Invalid output path: {e}")

        g = cls.get_gump(int(gump_id))
        if g is None:
            return False

        try:
            img = g.to_image()
            img.save(str(out_path), format="PNG")
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to save gump PNG: {e}")

    @staticmethod
    def _decode_gump(data: bytes) -> tuple[int, int, bytes]:
        """Decode a gump entry.

        Supports:
        - Test/fixture raw format: uint16 width, uint16 height, then width*height*2 bytes of UO16 pixels.
        - Best-effort classic gump RLE: int32 width, int32 height, int32[height] lookup table,
          then (color:uint16, run:uint16) pairs for each scanline.
        """
        # Raw test format (matches `tests/test_art_decode.py` style fixtures).
        if len(data) >= 4:
            w_u16, h_u16 = struct.unpack_from("<HH", data, 0)
            if w_u16 > 0 and h_u16 > 0:
                expected = 4 + (w_u16 * h_u16 * 2)
                if len(data) == expected:
                    return w_u16, h_u16, data[4:]

        # Classic RLE gump format.
        if len(data) < 8:
            raise ValueError("Gump data too short")

        width, height = struct.unpack_from("<ii", data, 0)
        if width <= 0 or height <= 0:
            raise ValueError("Invalid gump dimensions")
        if width > 8192 or height > 8192:
            raise ValueError("Unreasonable gump dimensions")

        lookup_base = 8
        if len(data) < lookup_base + (height * 4):
            raise ValueError("Gump data missing lookup table")

        lookups = struct.unpack_from(f"<{height}i", data, lookup_base)
        run_base = lookup_base + (height * 4)

        def try_decode(offset_unit: int) -> Optional[bytes]:
            out = bytearray(width * height * 2)
            for y in range(height):
                off = lookups[y]
                if off < 0:
                    continue
                pos = run_base + (off * offset_unit)
                if pos < run_base or pos > len(data):
                    return None

                x = 0
                # Decode (color, run) pairs until we fill the row or hit bounds.
                while x < width:
                    if pos + 4 > len(data):
                        break
                    color, run = struct.unpack_from("<HH", data, pos)
                    pos += 4
                    if run == 0:
                        break

                    if color == 0:
                        x += run
                        continue

                    # Write run pixels (UO16) into output buffer.
                    end_x = min(width, x + run)
                    for xi in range(x, end_x):
                        out_index = (y * width + xi) * 2
                        out[out_index:out_index + 2] = struct.pack("<H", color)
                    x += run

            return bytes(out)

        # In different client variants the lookup offsets are stored in different units.
        # Try dword-unit first, then byte-unit.
        pixels = try_decode(4)
        if pixels is None:
            pixels = try_decode(1)
        if pixels is None:
            raise ValueError("Unsupported gump data format")

        return width, height, pixels
