"""
RadarCol module - Manages radar color data.
"""

from typing import List, Tuple
from .binary_extensions import BinaryReader
from .files import Files
from .exceptions import FileAccessException


class RadarCol:
    """Static class for managing radar colors."""

    _colors: List[Tuple[int, int, int]] = []
    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """Initialize radar color data."""
        if cls._initialized:
            return True

        try:
            path = Files.get_file_path("radarcol.mul")
            if path:
                cls._load_colors(path)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize radarcol: {e}")

        return False

    @classmethod
    def _load_colors(cls, path: str) -> None:
        """Load color data."""
        with open(path, 'rb') as f:
            reader = BinaryReader(f)
            # Each color is typically 2 bytes (16-bit color)
            while True:
                try:
                    color = reader.read_uint16()
                    cls._colors.append(color)
                except Exception:
                    break

    @classmethod
    def get_color(cls, index: int) -> int:
        """Get color by index."""
        if not cls._initialized:
            cls.initialize()

        if 0 <= index < len(cls._colors):
            return cls._colors[index]
        return 0
