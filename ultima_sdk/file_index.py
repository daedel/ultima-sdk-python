"""
FileIndex module - Manages indexed file access for .mul files.
"""

from dataclasses import dataclass
from typing import List, Optional
from .binary_extensions import BinaryReader


@dataclass
class FileIndexEntry:
    """Representation of a file index entry."""
    index: int
    offset: int
    size: int


class IndexEntry:
    """Single file index entry."""

    def __init__(self, offset: int, size: int, extra: int = 0):
        self.offset = offset
        self.size = size
        self.extra = extra


class FileIndex:
    """Manages indexed file access."""

    def __init__(self, idx_path: str, mul_path: str):
        self.idx_path = idx_path
        self.mul_path = mul_path
        self.entries: list = []
        self._load_index()

    def _load_index(self) -> None:
        """Load index file."""
        try:
            with open(self.idx_path, 'rb') as f:
                reader = BinaryReader(f)
                while True:
                    try:
                        offset = reader.read_uint32()
                        size = reader.read_uint32()
                        extra = reader.read_uint32()
                        self.entries.append(IndexEntry(offset, size, extra))
                    except Exception:
                        break
        except Exception:
            pass

    def add_entry(self, index: int, offset: int, size: int) -> None:
        self.entries.append(FileIndexEntry(index=index, offset=offset, size=size))

    def get_entry(self, index: int) -> Optional[IndexEntry]:
        """Get index entry by index."""
        if 0 <= index < len(self.entries):
            return self.entries[index]
        return None

    def read_entry(self, index: int) -> Optional[bytes]:
        """Read data for index entry."""
        entry = self.get_entry(index)
        if not entry:
            return None

        try:
            with open(self.mul_path, 'rb') as f:
                f.seek(entry.offset)
                return f.read(entry.size)
        except Exception:
            return None
