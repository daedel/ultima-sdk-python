"""Tests for file_index module."""

import pytest
# from pathlib import Path
from ultima_sdk.file_index import FileIndex, FileIndexEntry
from ultima_sdk.exceptions import FileParseError


class TestFileIndexEntry:
    """Test FileIndexEntry class."""

    def test_initialization(self) -> None:
        """Test entry creation."""
        entry = FileIndexEntry(offset=100, length=50, extra=0)
        assert entry.offset == 100
        assert entry.length == 50
        assert entry.extra == 0

    @pytest.mark.parametrize("offset,length,extra", [
        (-1, 50, 0),  # Negative offset
        (100, -1, 0),  # Negative length
    ])
    def test_invalid_values(self, offset: int, length: int, extra: int) -> None:
        """Test invalid offset/length raises ValueError."""
        with pytest.raises(ValueError):
            FileIndexEntry(offset, length, extra)


class TestFileIndex:
    """Test FileIndex class."""

    @pytest.fixture
    def sample_index_data(self) -> bytes:
        """Sample binary data for index."""
        # Mock 3 entries: offset=0, length=100, extra=0; etc.
        return b'\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00' * 3

    def test_load_from_bytes(self, sample_index_data: bytes) -> None:
        """Test loading index from bytes."""
        index = FileIndex()
        index.load_from_bytes(sample_index_data)
        assert len(index.entries) == 3
        assert index.entries[0].offset == 0
        assert index.entries[0].length == 100

    def test_load_invalid_data(self) -> None:
        """Test loading invalid data raises FileParseError."""
        index = FileIndex()
        with pytest.raises(FileParseError):
            index.load_from_bytes(b'invalid')

    def test_get_entry(self, sample_index_data: bytes) -> None:
        """Test retrieving an entry by index."""
        index = FileIndex()
        index.load_from_bytes(sample_index_data)
        entry = index.get_entry(1)
        assert entry.offset == 0  # Assuming sequential
        assert entry.length == 100

    def test_get_entry_out_of_range(self, sample_index_data: bytes) -> None:
        """Test out-of-range index raises IndexError."""
        index = FileIndex()
        index.load_from_bytes(sample_index_data)
        with pytest.raises(IndexError):
            index.get_entry(10)
