"""Tests for art module."""

import struct

from ultima_sdk.art import Art


class TestArt:
    """Tests for the Art static class."""

    def setup_method(self) -> None:
        """Reset Art state before each test."""
        Art._initialized = False
        Art._index = None
        Art._patch_cache = {}

    # ------------------------------------------------------------------
    # Land tile tests
    # ------------------------------------------------------------------

    def _make_land_tile_bytes(self) -> bytes:
        """Build a minimal valid land tile pixel buffer (44 rows, diamond)."""
        parts = []
        row_widths = list(range(2, 46, 2)) + list(range(44, 0, -2))
        for w in row_widths:
            for _ in range(w):
                parts.append(struct.pack("<H", 0x8001))  # opaque pixel
        return b"".join(parts)

    def test_get_land_tile_from_patch_cache(self) -> None:
        """get_land_tile() should use patch cache when populated."""
        Art._initialized = True
        raw = self._make_land_tile_bytes()
        Art._patch_cache[0] = raw
        result = Art.get_land_tile(0)
        assert result is not None
        assert len(result) == 44
        assert len(result[0]) == 44

    def test_get_land_tile_returns_none_when_empty(self) -> None:
        """get_land_tile() returns None when no data is available."""
        Art._initialized = True  # Skip file init
        Art._index = None
        Art._patch_cache = {}
        result = Art.get_land_tile(0)
        assert result is None

    def test_land_row_widths_shape(self) -> None:
        """LAND_ROW_WIDTHS should have 44 entries summing to 44*44//2 pixels."""
        assert len(Art.LAND_ROW_WIDTHS) == 44
        # Diamond sum: sum(range(2,46,2)) + sum(range(44,0,-2)) = 22*23 + 22*23 - 44 =         assert sum(Art.LAND_ROW_WIDTHS) == 1012
        assert sum(Art.LAND_ROW_WIDTHS) == 1012
        assert Art.LAND_ROW_WIDTHS[0] == 2
        assert Art.LAND_ROW_WIDTHS[21] == 44
        assert Art.LAND_ROW_WIDTHS[43] == 2

    # ------------------------------------------------------------------
    # Static tile tests
    # ------------------------------------------------------------------

    def _make_static_tile_bytes(self, width: int = 4, height: int = 3) -> bytes:
        """Build a minimal valid static tile buffer.

        Layout (per art.py get_static_tile):
          4-byte header (skip)
          uint16 width, uint16 height
          height x uint16 lookup_offsets  (ushort index relative to pixel_data_start)
          RLE rows: each row is (x_offset: uint16, run: uint16, run*uint16 pixels)
                    followed by (0, 0) sentinel
        """
        # Build RLE row bytes first
        row_parts = []
        for _ in range(height):
            # Single run: x_offset=0, run=width, then width pixels, then (0,0) sentinel
            row = struct.pack("<HH", 0, width)
            for _ in range(width):
                row += struct.pack("<H", 0x8001)  # opaque pixel
            row += struct.pack("<HH", 0, 0)        # sentinel
            row_parts.append(row)

        # Lookup offsets are ushort indices relative to pixel_data_start.
        # pixel_data_start = 4 (header) + 4 (dims) + height*2 (lookup table)
        # RLE data sits immediately after the lookup table (= at pixel_data_start).
        offsets = []
        current = 0  # byte offset from pixel_data_start
        for rp in row_parts:
            offsets.append(current // 2)  # ushort index
            current += len(rp)

        buf = bytearray()
        buf += b"\x00" * 4                         # 4-byte header (skip)
        buf += struct.pack("<HH", width, height)    # dims
        for o in offsets:
            buf += struct.pack("<H", o)             # lookup table
        for rp in row_parts:
            buf += rp                               # RLE data
        return bytes(buf)

    def test_get_static_tile_from_patch_cache(self) -> None:
        """get_static_tile() should use patch cache when populated."""
        Art._initialized = True
        raw = self._make_static_tile_bytes(4, 3)
        tile_id = 5
        Art._patch_cache[tile_id + 0x4000] = raw
        result = Art.get_static_tile(tile_id)
        assert result is not None
        pixels, width, height = result
        assert width == 4
        assert height == 3
        assert len(pixels) == 3
        assert len(pixels[0]) == 4

    def test_get_static_tile_returns_none_when_empty(self) -> None:
        """get_static_tile() returns None when no data is available."""
        Art._initialized = True
        Art._index = None
        Art._patch_cache = {}
        result = Art.get_static_tile(0)
        assert result is None

    def test_get_static_tile_opaque_pixels(self) -> None:
        """Opaque pixels should have 0x8000 set."""
        Art._initialized = True
        raw = self._make_static_tile_bytes(2, 2)
        tile_id = 1
        Art._patch_cache[tile_id + 0x4000] = raw
        result = Art.get_static_tile(tile_id)
        assert result is not None
        pixels, w, h = result
        # All non-zero pixels should have bit 15 set
        for row in pixels:
            for px in row:
                if px != 0:
                    assert px & 0x8000, f"Expected opaque bit set, got 0x{px:04x}"

    # ------------------------------------------------------------------
    # apply_verdata_patch tests
    # ------------------------------------------------------------------

    def test_apply_verdata_patch_land(self) -> None:
        """apply_verdata_patch() stores data under block_id for land tiles."""
        Art._initialized = True
        raw = self._make_land_tile_bytes()
        Art.apply_verdata_patch(10, raw)
        assert Art._patch_cache[10] == raw

    def test_apply_verdata_patch_static(self) -> None:
        """apply_verdata_patch() stores data under block_id for static tiles."""
        Art._initialized = True
        raw = self._make_static_tile_bytes()
        block_id = 0x4000 + 7
        Art.apply_verdata_patch(block_id, raw)
        assert Art._patch_cache[block_id] == raw

    def test_apply_verdata_patch_with_extra(self) -> None:
        """apply_verdata_patch() stores extra under (block_id, 'extra') when provided."""
        Art._initialized = True
        raw = b"\x00" * 8
        block_id = 0x4000 + 3
        extra = (44 << 16) | 44
        Art.apply_verdata_patch(block_id, raw, extra)
        assert Art._patch_cache[(block_id, 'extra')] == extra
