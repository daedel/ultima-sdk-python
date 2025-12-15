"""
FileIndex module - Manages indexed file access for .mul files.
"""

from dataclasses import dataclass
from typing import List, Optional
from .binary_extensions import BinaryReader
from .exceptions import FileParseError
from io import BytesIO
import warnings


@dataclass
class FileIndexEntry:
    """Representation of a file index entry used by tests.

    Fields: offset (int), length (int), extra (int).
    Validates non-negative values.
    """
    offset: int
    length: int
    extra: int = 0

    def __post_init__(self) -> None:
        if self.offset < 0 or self.length < 0:
            raise ValueError("offset and length must be non-negative")


class IndexEntry:
    """Internal index entry used by FileIndex when loading from disk."""

    def __init__(self, offset: int, size: int, extra: int = 0):
        self.offset = offset
        self.size = size
        self.extra = extra


class FileIndex:
    """Manages indexed file access.

    Tests expect a no-arg constructor and a `load_from_bytes()` helper
    to populate `entries` from raw index data.
    """

    def __init__(self, idx_path: Optional[str] = None, mul_path: Optional[str] = None):
        self.idx_path = idx_path
        self.mul_path = mul_path
        self.entries: List[IndexEntry] = []
        if idx_path and mul_path:
            self._load_index()

    def _load_index(self) -> None:
        """Load index from `self.idx_path` on disk."""
        try:
            with open(self.idx_path, 'rb') as f:
                reader = BinaryReader(f)
                while True:
                    try:
                        offset = reader.read_uint32()
                        size = reader.read_uint32()
                        extra = reader.read_uint32()
                        self.entries.append(IndexEntry(offset, size, extra))
                    except EOFError:
                        break
        except FileNotFoundError:
            raise FileParseError("Index file not found", file_path=self.idx_path)

    def load_from_bytes(self, data: bytes) -> None:
        """Load index entries from a bytes buffer.

        Expects sequences of three uint32 values (offset, length, extra).
        Raises `FileParseError` on malformed input.
        """
        self.entries = []
        # Each index entry is 12 bytes (3 x uint32). Reject malformed lengths.
        if len(data) % 12 != 0:
            raise FileParseError("Invalid index data")
        try:
            reader = BinaryReader(BytesIO(data))
            while True:
                try:
                    offset = reader.read_uint32()
                    length = reader.read_uint32()
                    extra = reader.read_uint32()
                    self.entries.append(FileIndexEntry(offset=offset, length=length, extra=extra))
                except EOFError:
                    break
        except EOFError:
            raise FileParseError("Invalid index data")
        except Exception as e:
            raise FileParseError("Invalid index data") from e

    def add_entry(self, index: int, offset: int, size: int) -> None:
        self.entries.append(IndexEntry(offset, size))

    def get_entry(self, index: int) -> IndexEntry:
        """Get index entry by index, raise IndexError if out of range."""
        if 0 <= index < len(self.entries):
            return self.entries[index]
        raise IndexError("index out of range")

    def read_entry(self, index: int) -> Optional[bytes]:
        """Read data for index entry from associated mul file if available."""
        entry = self.get_entry(index)
        try:
            with open(self.mul_path, 'rb') as f:
                f.seek(entry.offset)
                return f.read(entry.length)
        except Exception:
            return None
