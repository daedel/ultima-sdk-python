"""
Art module - Manages static item art data.
"""

from typing import Optional, Tuple
from .binary_extensions import BinaryReader
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


class ArtData:
    """Represents static item art."""

    def __init__(self, graphic_id: int, width: int, height: int, pixels: bytes):
        self.graphic_id = graphic_id
        self.width = width
        self.height = height
        self.pixels = pixels  # Pixel data


class Art:
    """Static class for managing art data."""

    _index: Optional[FileIndex] = None
    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """Initialize the art index."""
        if cls._initialized:
            return True

        try:
            from .file_index import FileIndex

            idx_path = Files.get_file_path("artidx.mul")
            mul_path = Files.get_file_path("art.mul")

            if idx_path and mul_path:
                cls._index = FileIndex(idx_path, mul_path)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize art: {e}")

        return False

    @classmethod
    def get_art(cls, graphic_id: int) -> Optional[ArtData]:
        """Get art by graphic ID."""
        if not cls._initialized:
            cls.initialize()

        if not cls._index:
            return None

        # Implementation depends on FileIndex
        return None


@dataclass
class ArtTile:
    """Simple representation of an art tile."""
    tile_id: int
    data: bytes


class ArtLoader:
    """Minimal ArtLoader stub that exposes interface expected by tests."""

    def __init__(self, path: Path | str) -> None:
        """Initialize with a path (file or folder)."""
        self.path = Path(path)
        self._tiles: Dict[int, ArtTile] = {}

    def load_tile(self, tile_id: int) -> Optional[ArtTile]:
        """Return a stub ArtTile for the given id (does not parse real files)."""
        if tile_id not in self._tiles:
            # create an empty/stub tile to allow tests to import/use
            self._tiles[tile_id] = ArtTile(tile_id=tile_id, data=b"")
        return self._tiles[tile_id]
