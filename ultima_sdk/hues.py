"""
Hues module - Manages color palette data.
"""

from typing import List, Optional
from .binary_extensions import BinaryReader
from .files import Files
from .exceptions import FileAccessException


class HueEntry:
    """Represents a single hue color entry."""

    def __init__(self, colors: List[int]):
        self.colors = colors  # List of 16 RGB values

    def get_color(self, index: int) -> Optional[int]:
        """Get color at index."""
        if 0 <= index < len(self.colors):
            return self.colors[index]
        return None


class Hues:
    """Static class for managing hue data."""

    _hues: List[HueEntry] = []
    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """Load hue data from file."""
        if cls._initialized:
            return True

        try:
            path = Files.get_file_path("hues.mul")
            if not path:
                return False

            with open(path, 'rb') as f:
                reader = BinaryReader(f)
                cls._load_hues(reader)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to load hues.mul: {e}")

    @classmethod
    def _load_hues(cls, reader: BinaryReader) -> None:
        """Load all hue data."""
        # Hue file typically contains 3000 hues
        for _ in range(3000):
            colors = [reader.read_uint16() for _ in range(16)]
            cls._hues.append(HueEntry(colors))

    @classmethod
    def get_hue(cls, id: int) -> Optional[HueEntry]:
        """Get hue by ID."""
        if not cls._initialized:
            cls.initialize()

        if 0 <= id < len(cls._hues):
            return cls._hues[id]
        return None

    @classmethod
    def count(cls) -> int:
        """Get number of hues."""
        if not cls._initialized:
            cls.initialize()
        return len(cls._hues)
