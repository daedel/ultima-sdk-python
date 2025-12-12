"""
Map module - Manages map and terrain data.
"""

from typing import Optional, List, Tuple
from .tile_matrix import TileMatrix
from .files import Files
from .exceptions import FileAccessException


class MapData:
    """Represents map terrain data."""

    def __init__(self, map_id: int):
        self.map_id = map_id
        self.tile_matrix: Optional[TileMatrix] = None

    def get_tile(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Get tile ID and altitude at coordinates."""
        if self.tile_matrix:
            return self.tile_matrix.get_tile(x, y)
        return None


class Map:
    """Static class for managing map data."""

    _maps: List[MapData] = []
    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """Initialize map data."""
        if cls._initialized:
            return True

        try:
            cls._load_maps()
            cls._initialized = True
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize map: {e}")

    @classmethod
    def _load_maps(cls) -> None:
        """Load all map data."""
        # Load all map files
        for i in range(6):
            map_file = f"map{i}.mul"
            path = Files.get_file_path(map_file)
            if path:
                map_data = MapData(i)
                cls._maps.append(map_data)

    @classmethod
    def get_map(cls, map_id: int) -> Optional[MapData]:
        """Get map data by ID."""
        if not cls._initialized:
            cls.initialize()

        if 0 <= map_id < len(cls._maps):
            return cls._maps[map_id]
        return None
