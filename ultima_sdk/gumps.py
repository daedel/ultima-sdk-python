"""
Gumps module - Reads gump images from gumpart.mul / gumpart.idx.

RLE format (each row):
  Lookup table: height ushort values, each is a ushort-array index into the
                RLE data (multiply by 2 to get byte offset from data start).
  RLE stream:   pairs of (color: ushort, run: ushort)  — color FIRST per C# ref.

Width and height come from the INDEX extra field, NOT from the data block.
  extra >> 16 & 0xFFFF  = width
  extra & 0xFFFF        = height

Every non-zero color must have bit 15 (0x8000) set for the display layer
to treat it as opaque (15-bit RGB, bit-15 = opacity).
"""

import struct
from typing import Optional, Tuple, List
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException


class Gumps:
    """Static class for loading gump images."""

    _index: Optional[FileIndex] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> bool:
        if cls._initialized:
            return True
        try:
            idx_path = Files.get_file_path("gumpidx.mul")
            mul_path = Files.get_file_path("gumpart.mul")
            if not idx_path or not mul_path:
                return False
            cls._index = FileIndex(idx_path, mul_path, entry_size=12)
            cls._initialized = True
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize Gumps: {e}")

    @classmethod
    def get_gump(
        cls, id: int
    ) -> Optional[Tuple[List[List[int]], int, int]]:
        """Return (pixels_2d, width, height) for gump *id*, or None.

        pixels_2d is a list of *height* rows, each a list of *width* ushort
        color values with bit 15 set for opaque pixels (0 = transparent).
        """
        if not cls._initialized:
            cls.initialize()
        if cls._index is None:
            return None

        # read_raw must return (data_bytes, extra) so we can get w/h.
        result = cls._index.read_raw(id)
        if result is None:
            return None
        data, extra = result  # extra is the 3rd int32 from the .idx entry

        # Width and height are packed into the extra field.
        width  = (extra >> 16) & 0xFFFF
        height = extra & 0xFFFF
        if width == 0 or height == 0:
            return None

        # The data block begins with a lookup table: height × ushort values.
        # Each value is a ushort-array index; multiply by 2 → byte offset
        # from the start of the RLE data (i.e. from byte 0 of `data`).
        lookup_count = height
        lookup_bytes = lookup_count * 2
        if len(data) < lookup_bytes:
            return None

        lookups = struct.unpack_from(f"<{lookup_count}H", data, 0)
        rle_data = data  # row offsets are relative to data[0], ushort-indexed

        pixels = []
        for y in range(height):
            row_byte_offset = lookups[y] * 2   # ushort index → byte offset
            pos = row_byte_offset
            row: List[int] = []
            cur_x = 0
            while cur_x < width:
                if pos + 4 > len(rle_data):
                    break
                # C# order: color = dat[count++]; run = dat[count++]
                color, run = struct.unpack_from("<HH", rle_data, pos)
                pos += 4
                if run == 0:
                    # Explicit zero-run — advance to end of row
                    break
                # Set bit 15 (opaque) on non-zero colors
                if color != 0:
                    color ^= 0x8000
                row.extend([color] * run)
                cur_x += run
            # Pad row to exact width if data was short
            if len(row) < width:
                row.extend([0] * (width - len(row)))
            pixels.append(row[:width])

        return pixels, width, height
