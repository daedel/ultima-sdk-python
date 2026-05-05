""" Gumps module - Reads gump images from gumpart.mul / gumpart.idx.

RLE format (each row):
    Lookup table: height ushort values, each is a ushort-array index into the
                  RLE data (multiply by 2 to get byte offset from data start).
    RLE stream:   pairs of (color: ushort, run: ushort) -- color FIRST per C# ref.

Width and height come from the INDEX extra field, NOT from the data block.
    extra >> 16 & 0xFFFF = width
    extra & 0xFFFF       = height

Every non-zero color must have bit 15 (0x8000) set for the display layer
to treat it as opaque (15-bit RGB, bit-15 = opacity).
"""

import struct
from typing import Optional, Tuple, List
from pathlib import Path

from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException


class Gumps:
    """Static class for loading gump images."""

    _index: Optional[FileIndex] = None
    _initialized: bool = False

    # Overlay cache: maps gump id -> (raw_bytes, extra) from verdata patches.
    _patch_cache: dict = {}

    @classmethod
    def initialize(cls, idx_path: Optional[str] = None, mul_path: Optional[str] = None) -> bool:
        """Initialize Gumps static state. Optionally accepts paths for testing."""
        if cls._initialized and not idx_path and not mul_path:
            return True
        try:
            idx_path = idx_path or Files.get_file_path("gumpidx.mul")
            mul_path = mul_path or Files.get_file_path("gumpart.mul")
            if not idx_path or not mul_path:
                return False
            cls._index = FileIndex(idx_path, mul_path, entry_size=12)
            cls._initialized = True
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize Gumps: {e}")

    @classmethod
    def save_png(cls, id: int, path: str | Path) -> bool:
        """Render gump to PNG file."""
        data = cls.get_gump(id)
        if data is None: return False
        try:
            from PIL import Image
            pixels, w, h = data
            img = Image.new("RGBA", (w, h))
            img.save(path, "PNG")
            return True
        except Exception: return False

    @classmethod
    def get_gump(
        cls, id: int
    ) -> Optional[Tuple[List[List[int]], int, int]]:
        """Return (pixels_2d, width, height) for gump *id*, or None.
        pixels_2d is a list of *height* rows, each a list of *width* ushort color
        values with bit 15 set for opaque pixels (0 = transparent).
        """
        if not cls._initialized:
            cls.initialize()

        # Check verdata patch cache first, then fall through to index.
        if id in cls._patch_cache:
            data, extra = cls._patch_cache[id]
        else:
            if cls._index is None:
                return None

            # Use read_raw_with_extra() so we get both data bytes AND the
            # index extra field (which encodes width and height for gumps).
            result = cls._index.read_raw_with_extra(id)
            if result is None:
                return None
            data, extra = result

        # Width and height are packed into the extra field.
        width = (extra >> 16) & 0xFFFF
        height = extra & 0xFFFF

        if width == 0 or height == 0:
            return None

        # The data block begins with a lookup table: height x ushort values.
        # Each value is a ushort-array index; multiply by 2 -> byte offset
        # from the start of the RLE data (i.e. from byte 0 of `data`).
        lookup_count = height
        lookup_bytes = lookup_count * 2
        if len(data) < lookup_bytes:
            return None

        lookups = struct.unpack_from(f"<{lookup_count}H", data, 0)
        rle_data = data  # row offsets are relative to data[0], ushort-indexed

        pixels = []
        for y in range(height):
            row_byte_offset = lookups[y] * 2  # ushort index -> byte offset
            pos = row_byte_offset
            row: List[int] = []
            cur_x = 0
            while cur_x < width:
                if pos + 4 > len(rle_data):
                    break

                # C# order: color = dat[count++]; run = dat[count++]
                color, run = struct.unpack_from("<HH", rle_data, pos)
                pos += 4

                if color != 0:
                    color |= 0x8000

                for _ in range(run):
                    if cur_x >= width:
                        break
                    row.append(color)
                    cur_x += 1

            # Pad any short rows with transparent pixels.
            while len(row) < width:
                row.append(0)

            pixels.append(row)

        return pixels, width, height

    @classmethod
    def apply_verdata_patch(cls, block_id: int, data: bytes, extra: int) -> None:
        """Cache raw verdata patch bytes for a gump."""
        if not cls._initialized:
            cls.initialize()
        cls._patch_cache[block_id] = (data, extra)
