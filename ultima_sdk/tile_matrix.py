"""
TileMatrix module - Manages tile matrix data for maps.
"""

from typing import Optional, Tuple


class TileMatrix:
    """Represents a tile matrix for a map."""

    def __init__(self, map_id: int, width: int, height: int):
        self.map_id = map_id
        self.width = width
        self.height = height
        self.tiles: list = []

    def get_tile(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Get tile ID and altitude at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = y * self.width + x
            if idx < len(self.tiles):
                return self.tiles[idx]
        return None

    def set_tile(self, x: int, y: int, tile_id: int, altitude: int) -> None:
        """Set tile data at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = y * self.width + x
            while len(self.tiles) <= idx:
                self.tiles.append((0, 0))
            self.tiles[idx] = (tile_id, altitude)
