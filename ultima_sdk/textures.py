"""
Textures module - Manages landscape texture data.
"""

from typing import Optional, List
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException


class TextureData:
    """Represents a texture."""

    def __init__(self, texture_id: int, width: int, height: int, pixels: bytes):
        self.texture_id = texture_id
        self.width = width
        self.height = height
        self.pixels = pixels


class Textures:
    """Static class for managing texture data."""

    _index: Optional[FileIndex] = None
    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """Initialize texture index."""
        if cls._initialized:
            return True

        try:
            idx_path = Files.get_file_path("texidx.mul")
            mul_path = Files.get_file_path("texmaps.mul")

            if idx_path and mul_path:
                from .file_index import FileIndex
                cls._index = FileIndex(idx_path, mul_path)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize textures: {e}")

        return False

    @classmethod
    def get_texture(cls, texture_id: int) -> Optional[TextureData]:
        """Get texture by ID."""
        if not cls._initialized:
            cls.initialize()

        return None
