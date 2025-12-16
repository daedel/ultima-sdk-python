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
class IndexEntry:
    """Internal index entry used by FileIndex.

    Note: Disk-backed index formats commonly use signed int32 values where -1
    indicates a missing entry. This class intentionally does not validate.
    """

    offset: int
    length: int
    extra: int = 0

    @property
    def size(self) -> int:
        return self.length


@dataclass
class FileIndexEntry(IndexEntry):
    """Representation of a file index entry used by tests.

    Validates non-negative values.
    """

    def __post_init__(self) -> None:
        if self.offset < 0 or self.length < 0:
            raise ValueError("offset and length must be non-negative")


class FileIndex:
    """Manages indexed file access.

    Tests expect a no-arg constructor and a `load_from_bytes()` helper
    to populate `entries` from raw index data.
    """

    def __init__(
        self,
        idx_path: Optional[str] = None,
        mul_path: Optional[str] = None,
        file_id: Optional[int] = None,
    ):
        self.idx_path = idx_path
        self.mul_path = mul_path
        self.file_id = file_id
        self.entries: List[IndexEntry] = []
        if idx_path and mul_path:
            self._load_index()

    def _load_index(self) -> None:
        """Load index from `self.idx_path` on disk."""
        idx_path = self.idx_path
        if idx_path is None:
            raise FileParseError("Index file path is not set", file_path=idx_path)
        try:
            with open(idx_path, 'rb') as f:
                reader = BinaryReader(f)
                while True:
                    try:
                        # Many MUL idx formats store signed int32 values where -1
                        # indicates a missing entry.
                        offset = reader.read_int32()
                        length = reader.read_int32()
                        extra = reader.read_int32()
                        self.entries.append(IndexEntry(offset, length, extra))
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

    def read_raw(self, index: int) -> Optional[bytes]:
        """Read raw bytes for an entry from the associated mul file.

        Returns None for missing entries (e.g. offset < 0 or length <= 0).
        """
        if index is None or index < 0:
            return None

        # verdata.mul overrides: allow patched blocks to supersede idx/mul.
        # Import locally to avoid a hard dependency/cycle at import time.
        if self.file_id is not None:
            try:
                from .verdata import Verdata

                patch = Verdata.read_patch(self.file_id, index)
                if patch is not None:
                    return patch
            except Exception:
                # If verdata is unreadable, fall back to base MUL.
                pass

        try:
            entry = self.get_entry(index)
        except IndexError:
            return None
        if entry.offset is None or entry.length is None:
            return None
        if entry.offset < 0 or entry.length <= 0:
            return None
        if not self.mul_path:
            return None

        try:
            with open(self.mul_path, 'rb') as f:
                f.seek(entry.offset)
                return f.read(entry.length)
        except Exception:
            return None

    # Backward compatible alias
    def read_entry(self, index: int) -> Optional[bytes]:
        return self.read_raw(index)
