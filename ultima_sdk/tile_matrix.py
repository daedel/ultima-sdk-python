"""
TileMatrix module - Manages tile matrix data for maps.
"""

from typing import Optional, Tuple

import os
import struct
from functools import lru_cache


class TileMatrix:
    """Represents a tile matrix for a map."""

    def __init__(self, map_id: int, width: int, height: int, map_path: str | None = None):
        self.map_id = map_id
        self.width = width
        self.height = height
        self.tiles: list = []
        self.map_path = map_path

        self.block_width = width >> 3
        self.block_height = height >> 3

        # Cache decoded 8x8 land blocks.
        self._land_block_cache: dict[tuple[int, int], list[tuple[int, int]]] = {}

    def get_tile(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Get tile ID and altitude at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.map_path:
                return self._get_tile_from_map_file(x, y)

            idx = y * self.width + x
            if idx < len(self.tiles):
                return self.tiles[idx]
        return None

    def _get_tile_from_map_file(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        if not self.map_path or not os.path.exists(self.map_path):
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

        # Map block ordering is column-major by x-block then y-block:
        # offset = (((bx * BlockHeight) + by) * 196) + 4
        block_index = (bx * self.block_height) + by
        base = (block_index * 196) + 4

        block: list[tuple[int, int]] = [(0, 0)] * 64
        with open(self.map_path, "rb") as f:
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
