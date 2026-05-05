"""
Art module - Reads land tile and static item art from artidx.mul / art.mul
(or art.uop for High Seas clients).

Land tile geometry:
  44 rows arranged as an isometric diamond:
    top half:    row widths 2, 4, 6, ..., 44  (22 rows, step +2)
    bottom half: row widths 44, 42, ..., 2    (22 rows, step -2)
  Each row is left-padded so the diamond is centred in a 44×44 bounding box.
  Pixel values read directly from the stream, ORed with 0x8000 (opaque bit).

Static art:
  4-byte header (ignored), then standard RLE — the existing parsing is correct.
  Same 0x8000 alpha bit applies.
"""

import struct
from typing import Optional, List, Tuple
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException


class Art:
    """Static class for loading art tiles."""

    _index: Optional[FileIndex] = None
    _initialized: bool = False

    # Pre-computed land-tile row widths: 44 rows, diamond shape, step 2.
    # Top half: 2, 4, ..., 44  (indices 0-21)
    # Bottom half: 44, 42, ..., 2  (indices 22-43)
    LAND_ROW_WIDTHS: List[int] = (
        list(range(2, 46, 2))   # 2..44  — 22 values
        + list(range(44, 0, -2))  # 44..2  — 22 values
    )  # total 44 values; max = 44 ✓

    @classmethod
    def initialize(cls) -> bool:
        if cls._initialized:
            return True
        try:
            idx_path = Files.get_file_path("artidx.mul")
            mul_path = Files.get_file_path("art.mul")
            if not idx_path or not mul_path:
                return False
            cls._index = FileIndex(idx_path, mul_path, entry_size=12)
            cls._initialized = True
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize Art: {e}")

    # ------------------------------------------------------------------
    # Land tiles
    # ------------------------------------------------------------------

    @classmethod
    def get_land_tile(
        cls, id: int
    ) -> Optional[List[List[int]]]:
        """Return a 44-row list of pixel rows for land tile *id*.

        Each row contains the centred pixel values with bit 15 set (opaque).
        Transparent pixels (original value 0) remain 0.
        """
        if not cls._initialized:
            cls.initialize()
        if cls._index is None:
            return None

        data = cls._index.read_raw_data(id)
        if data is None:
            return None

        pos = 0
        rows: List[List[int]] = []

        for row_idx, row_width in enumerate(cls.LAND_ROW_WIDTHS):
            left_pad = (44 - row_width) // 2
            row: List[int] = [0] * 44

            for col in range(row_width):
                if pos + 2 > len(data):
                    break
                (pixel,) = struct.unpack_from("<H", data, pos)
                pos += 2
                if pixel != 0:
                    pixel |= 0x8000   # set opaque bit
                row[left_pad + col] = pixel

            rows.append(row)

        return rows

    # ------------------------------------------------------------------
    # Static (item) art
    # ------------------------------------------------------------------

    @classmethod
    def get_static_tile(
        cls, id: int
    ) -> Optional[Tuple[List[List[int]], int, int]]:
        """Return (pixels_2d, width, height) for static tile *id*, or None.

        Static art uses a 4-byte header followed by RLE rows.
        Each RLE entry is (offset: uint16, run: uint16, then *run* uint16 pixels).
        Non-zero pixels have 0x8000 OR'd in.
        """
        if not cls._initialized:
            cls.initialize()
        if cls._index is None:
            return None

        # id offset for statics in the combined art file
        data = cls._index.read_raw_data(id + 0x4000)
        if data is None or len(data) < 4:
            return None

        # 4-byte header (skip)
        pos = 4
        if pos + 4 > len(data):
            return None

        width, height = struct.unpack_from("<HH", data, pos)
        pos += 4
        if width == 0 or height == 0:
            return None

        # Lookup table: height × uint16 row offsets (byte offsets from table start)
        lookup_start = pos
        if pos + height * 2 > len(data):
            return None
        lookups = struct.unpack_from(f"<{height}H", data, pos)
        pos += height * 2

        pixel_data_start = pos  # RLE data starts here

        pixels: List[List[int]] = []
        for y in range(height):
            row: List[int] = [0] * width
            rle_pos = pixel_data_start + lookups[y] * 2  # ushort index → bytes
            x = 0
            while x < width:
                if rle_pos + 4 > len(data):
                    break
                offset, run = struct.unpack_from("<HH", data, rle_pos)
                rle_pos += 4
                if run == 0:
                    break
                x += offset
                for _ in range(run):
                    if rle_pos + 2 > len(data) or x >= width:
                        break
                    (pixel,) = struct.unpack_from("<H", data, rle_pos)
                    rle_pos += 2
                    if pixel != 0:
                        pixel |= 0x8000   # set opaque bit
                    row[x] = pixel
                    x += 1
            pixels.append(row)

        return pixels, width, height
