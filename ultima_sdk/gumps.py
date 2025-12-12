"""
Gumps module - Manages UI gump (interface) graphics.
"""

from typing import Optional
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException


class GumpData:
    """Represents a gump image."""

    def __init__(self, gump_id: int, width: int, height: int, pixels: bytes):
        self.gump_id = gump_id
        self.width = width
        self.height = height
        self.pixels = pixels


class Gumps:
    """Static class for managing gump data."""

    _index: Optional[FileIndex] = None
    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """Initialize gump index."""
        if cls._initialized:
            return True

        try:
            idx_path = Files.get_file_path("gumpidx.mul")
            mul_path = Files.get_file_path("gumpart.mul")

            if idx_path and mul_path:
                from .file_index import FileIndex
                cls._index = FileIndex(idx_path, mul_path)
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

        return None
