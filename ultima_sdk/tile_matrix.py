"""
TileMatrix module - Manages tile matrix data for maps.
"""

from typing import Optional, Tuple

import os
import struct
from functools import lru_cache


class TileMatrix:
    """Represents a tile matrix for a map."""

    def __init__(
        self,
        map_id: int,
        width: int,
        height: int,
        map_path: str | None = None,
        *,
        map_uop_path: str | None = None,
        map_uop_pattern: str | None = None,
    ):
        self.map_id = map_id
        self.width = width
        self.height = height
        self.tiles: list = []
        self.map_path = map_path

        self._uop = None
        self._uop_pattern = map_uop_pattern
        self._uop_segment_cache: dict[int, bytes] = {}

        if map_uop_path and map_uop_pattern:
            from .uop import UopFile

            self._uop = UopFile(map_uop_path, map_uop_pattern)

        # Verdata map patching is only standardized for map0 in this SDK mapping.
        self._verdata_file_id: int | None = None
        if map_id == 0:
            try:
                from .verdata_ids import IDS as VERDATA_IDS

                self._verdata_file_id = VERDATA_IDS.MAP0_MUL
            except Exception:
                self._verdata_file_id = None

        self.block_width = width >> 3
        self.block_height = height >> 3

        # Cache decoded 8x8 land blocks.
        self._land_block_cache: dict[tuple[int, int], list[tuple[int, int]]] = {}

    def get_tile(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Get tile ID and altitude at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.map_path or self._uop is not None:
                return self._get_tile_from_map_file(x, y)

            idx = y * self.width + x
            if idx < len(self.tiles):
                return self.tiles[idx]
        return None

    def _get_tile_from_map_file(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        if not self.map_path and not self._uop:
            return None

        if self.map_path and not os.path.exists(self.map_path):
            return None

        bx = x >> 3
        by = y >> 3
        if bx < 0 or by < 0 or bx >= self.block_width or by >= self.block_height:
            return None

        block = self._get_land_block(bx, by)
        ti = ((y & 0x7) << 3) + (x & 0x7)
        if 0 <= ti < 64:
            return block[ti]
        return None

    def _get_land_block(self, bx: int, by: int) -> list[tuple[int, int]]:
        key = (bx, by)
        cached = self._land_block_cache.get(key)
        if cached is not None:
            return cached

        # Map block ordering is column-major by x-block then y-block.
        block_index = (bx * self.block_height) + by

        block: list[tuple[int, int]] = [(0, 0)] * 64

        # Verdata override (map0 only per our mapping).
        if self._verdata_file_id is not None:
            try:
                from .verdata import Verdata

                patch = Verdata.read_patch(self._verdata_file_id, int(block_index))
            except Exception:
                patch = None

            if patch is not None and len(patch) >= 196:
                raw = patch[4:4 + (64 * 3)]
            else:
                raw = b""
        else:
            raw = b""

        if not raw:
            if self._uop is not None:
                # UOP map files store map data in chunks (virtual files) addressed by:
                # segment_id = block_index >> 12  (4096 blocks per chunk)
                # within = block_index & 0x0FFF
                segment_id = int(block_index >> 12)
                within = int(block_index & 0x0FFF)
                segment = self._uop_segment_cache.get(segment_id)
                if segment is None:
                    segment = self._uop.read_raw(segment_id) or b""
                    self._uop_segment_cache[segment_id] = segment

                base = (within * 196) + 4
                end = base + (64 * 3)
                raw = segment[base:end] if end <= len(segment) else b""
            else:
                base = (block_index * 196) + 4
                map_path = self.map_path
                if map_path is None:
                    raw = b""
                else:
                    with open(map_path, "rb") as f:
                        f.seek(base)
                        raw = f.read(64 * 3)

        if len(raw) != 64 * 3:
            self._land_block_cache[key] = block
            return block

        # Each tile: uint16 id, int8 z
        for i in range(64):
            tile_id, z = struct.unpack_from("<Hb", raw, i * 3)
            block[i] = (int(tile_id), int(z))

        self._land_block_cache[key] = block
        return block

    def set_tile(self, x: int, y: int, tile_id: int, altitude: int) -> None:
        """Set tile data at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = y * self.width + x
            while len(self.tiles) <= idx:
                self.tiles.append((0, 0))
            self.tiles[idx] = (tile_id, altitude)
