"""
StringList module - Manages localized string data.
"""

from typing import Dict, Optional
from .binary_extensions import BinaryReader
from .files import Files
from .exceptions import FileAccessException


def _decode_cliloc_text(data: bytes) -> str:
    # cliloc strings are typically UTF-8; be forgiving.
    return data.decode("utf-8", errors="replace").rstrip("\x00")


class StringEntry:
    """A single string entry."""

    def __init__(self, entry_id: int, text: str):
        self.entry_id = entry_id
        self.text = text


class StringList:
    """Static class for managing string lists."""

    _strings: Dict[int, StringEntry] = {}
    _initialized = False
    _source_path: Optional[str] = None

    @classmethod
    def initialize(cls, file_path: str | None = None) -> bool:
        """Initialize string data.

        Args:
            file_path: Optional explicit cliloc file path.
        """
        if cls._initialized:
            if file_path is None:
                return True
            if cls._source_path == file_path:
                return True

        try:
            cls._load_strings(file_path=file_path)
            cls._initialized = True
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize strings: {e}")

    @classmethod
    def _load_strings(cls, file_path: str | None = None) -> None:
        """Load string data from cliloc files."""
        cls._strings = {}

        if file_path is None:
            # Prefer English; fall back to other known names.
            candidates = [
                "cliloc.enu",
                "cliloc.deu",
                "cliloc.custom1",
                "cliloc.custom2",
            ]
            for name in candidates:
                candidate_path = Files.get_file_path(name)
                if candidate_path:
                    file_path = candidate_path
                    break

        if not file_path:
            cls._source_path = None
            return

        with open(file_path, "rb") as f:
            data = f.read()

        strings = cls._parse_cliloc_bytes(data)
        cls._strings = {k: StringEntry(k, v) for k, v in strings.items()}
        cls._source_path = file_path

    @staticmethod
    def _try_parse_with_header(data: bytes, header_bytes: int) -> Dict[int, str]:
        if header_bytes < 0 or header_bytes > len(data):
            raise ValueError("Invalid header length")

        reader = BinaryReader(data)
        if header_bytes:
            reader.seek(header_bytes)

        out: Dict[int, str] = {}
        # Entry layout (common): int32 id, byte flag, uint16 length, <length> bytes text
        while True:
            try:
                entry_id = reader.read_int32()
            except EOFError:
                break

            # Basic sanity (cliloc ids are non-negative in practice)
            if entry_id < 0:
                raise ValueError("Invalid cliloc entry id")

            _flag = reader.read_byte()
            length = reader.read_uint16()
            if length > 0x7FFF and length > len(data):
                raise ValueError("Unreasonable string length")
            text_bytes = reader.read(length)
            if len(text_bytes) != length:
                raise EOFError("Unexpected EOF in cliloc string")
            out[entry_id] = _decode_cliloc_text(text_bytes)

        # Require at least one entry to accept this parse.
        if not out:
            raise ValueError("No cliloc entries")

        return out

    @classmethod
    def _parse_cliloc_bytes(cls, data: bytes) -> Dict[int, str]:
        """Parse raw cliloc file bytes.

        Known variants include a small header (4 or 6 bytes) before entries.
        We try common header sizes and pick the first that parses cleanly.
        """
        # Commonly seen: int32 version + int16 language/unknown => 6 bytes
        header_candidates = [6, 4, 0]
        last_error: Exception | None = None
        for header in header_candidates:
            try:
                return cls._try_parse_with_header(data, header)
            except Exception as e:
                last_error = e
                continue
        raise ValueError("Unsupported cliloc format") from last_error

    @classmethod
    def get_string(cls, entry_id: int) -> Optional[str]:
        """Get string by entry ID."""
        if not cls._initialized:
            cls.initialize()

        if entry_id in cls._strings:
            return cls._strings[entry_id].text
        return None
