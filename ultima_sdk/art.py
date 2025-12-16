"""ultima_sdk.art

Manages static item art data.
"""

from typing import Optional, Tuple
from .binary_extensions import BinaryReader
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Protocol, runtime_checkable
import struct
from .exceptions import FileParseError
from .rendering import image_from_pixels


@runtime_checkable
class _ArtIndexLike(Protocol):
    """Structural type for index backends used by :class:`Art`.

    Both ``FileIndex`` and UOP-backed indexes provide a ``read_raw`` method.
    """

    def read_raw(self, index: int) -> Optional[bytes]:  # pragma: no cover
        ...


class ArtData:
    """Represents static item art."""

    def __init__(self, graphic_id: int, width: int, height: int, pixels: bytes):
        self.graphic_id = graphic_id
        self.width = width
        self.height = height
        self.pixels = pixels  # Pixel data

    def to_image(self):
        """Convert this art's pixels to a Pillow image.

        Supports RGB/RGBA buffers and common UO 16-bit pixels.
        """
        return image_from_pixels(self.width, self.height, self.pixels)


class Art:
    """Static class for managing art data."""

    _index: Optional[_ArtIndexLike] = None
    _initialized = False

    @classmethod
    def initialize(cls, idx_path: str | None = None, mul_path: str | None = None) -> bool:
        """Initialize the art index.

        Args:
            idx_path: Optional explicit path to art index file (artidx.mul).
            mul_path: Optional explicit path to art data file (art.mul).

        Returns:
            True if initialization succeeded.
        """
        if cls._initialized:
            return True

        try:
            from .file_index import FileIndex
            from .verdata_ids import IDS as VERDATA_IDS

            if idx_path is None:
                idx_path = Files.get_file_path("artidx.mul")
            if mul_path is None:
                mul_path = Files.get_file_path("art.mul")

            if idx_path and mul_path:
                cls._index = FileIndex(idx_path, mul_path, file_id=VERDATA_IDS.ART_MUL)
                cls._initialized = True
                return True

            # UOP fallback (newer clients).
            uop_path = Files.get_file_path("artlegacymul.uop")
            if uop_path:
                from .uop import UopBackedIndex

                cls._index = UopBackedIndex(
                    uop_path,
                    "build/artlegacymul/{0:D8}.tga",
                    has_extra=False,
                    file_id=VERDATA_IDS.ART_MUL,
                )
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

        raw = cls._index.read_raw(graphic_id)
        if not raw:
            return None

        # Try to decode as a "static" art entry first (width/height header).
        try:
            width, height, pixels_uo16 = cls._decode_static_art(raw)
            return ArtData(graphic_id=graphic_id, width=width, height=height, pixels=pixels_uo16)
        except Exception:
            pass

        # Fallback: some formats store land tiles as a fixed 44x44 block of 16-bit pixels.
        if len(raw) == 44 * 44 * 2:
            return ArtData(graphic_id=graphic_id, width=44, height=44, pixels=raw)

        raise FileParseError("Unsupported art data format")

    @classmethod
    def get_equipped_art(cls, item_id: int, *, body_id: int | None = None) -> Optional[ArtData]:
        """Get art for an equipped item, applying `equipconv.def` if available.

        This is a convenience wrapper for paperdoll/equipment rendering.
        It intentionally does not change `get_art()` behavior.
        """
        try:
            from .equipconv import EquipConv

            converted = EquipConv.convert(int(item_id), body_id=body_id)
        except Exception:
            converted = int(item_id)

        return cls.get_art(int(converted))

    @classmethod
    def save_png(cls, graphic_id: int, path, *, body_id: int | None = None) -> bool:
        """Save an art tile as a PNG.

        Args:
            graphic_id: The art/graphic id.
            path: Output file path (str or Path-like).
            body_id: If provided, uses `equipconv.def` conversion rules for equipped items.

        Returns:
            True if the art existed and was saved, False if the art id is missing.
        """
        try:
            from pathlib import Path

            out_path = Path(path)
        except Exception as e:
            raise FileAccessException(f"Invalid output path: {e}")

        data = cls.get_equipped_art(int(graphic_id), body_id=body_id) if body_id is not None else cls.get_art(int(graphic_id))
        if data is None:
            return False

        try:
            img = data.to_image()
            img.save(str(out_path), format="PNG")
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to save art PNG: {e}")

    @staticmethod
    def _decode_static_art(data: bytes) -> tuple[int, int, bytes]:
        """Decode a static art entry.

        Supports:
        - Raw format: uint16 width, uint16 height, then width*height*2 bytes of 16-bit pixels.
        - Classic UO RLE format: width/height + lookup table + run-length encoded scanlines.
        """
        # First, support the simplified "raw" format used by tests/fixtures:
        # uint16 width, uint16 height, then width*height*2 bytes of 16-bit pixels.
        if len(data) >= 4:
            raw_width, raw_height = struct.unpack_from("<HH", data, 0)
            if raw_width > 0 and raw_height > 0:
                expected_raw = 4 + (raw_width * raw_height * 2)
                if len(data) == expected_raw:
                    return raw_width, raw_height, data[4:]

        if len(data) < 8:
            raise FileParseError("Art data too short")

        # Common art.mul static format starts with:
        # int32 run_data_length, uint16 width, uint16 height
        run_data_length = struct.unpack_from("<I", data, 0)[0]
        width, height = struct.unpack_from("<HH", data, 4)
        if width <= 0 or height <= 0:
            raise FileParseError("Invalid art dimensions")
        if width > 4096 or height > 4096:
            raise FileParseError("Unreasonable art dimensions")

        # If the run-length header is clearly bogus, fail fast.
        if run_data_length > len(data):
            raise FileParseError("Unsupported art data format")

        # RLE format: after header+width+height comes a lookup table (height uint16 offsets)
        lookup_base = 8
        if len(data) < lookup_base + (height * 2):
            raise FileParseError("Art data missing lookup table")

        # Read lookup offsets (often stored as word offsets)
        lookups = struct.unpack_from(f"<{height}H", data, lookup_base)

        run_base = lookup_base + (height * 2)
        # Sanity: ensure the declared run-data length matches available bytes (best-effort)
        if run_base + run_data_length > len(data):
            # Some clients may not strictly match; clamp to available.
            run_data_length = max(0, len(data) - run_base)

        run_end = run_base + run_data_length

        out = bytearray(width * height * 2)

        for y in range(height):
            # In classic clients these offsets are word offsets into the run-data
            # stream (i.e., each unit is 2 bytes).
            pos = run_base + (lookups[y] * 2)
            if pos < run_base or pos >= run_end:
                # Fallback: some variants store byte offsets.
                alt = run_base + lookups[y]
                if alt < run_base or alt >= run_end:
                    continue
                pos = alt

            x = 0
            while True:
                if pos + 4 > run_end:
                    break

                # Packet header: x-offset delta, run length (both uint16).
                # The line ends with a (0, 0) sentinel.
                xoff, run = struct.unpack_from("<HH", data, pos)
                pos += 4
                if xoff == 0 and run == 0:
                    break

                x += xoff
                needed = run * 2
                if pos + needed > run_end:
                    break

                for _ in range(run):
                    if 0 <= x < width:
                        out_index = (y * width + x) * 2
                        out[out_index:out_index + 2] = data[pos:pos + 2]
                    pos += 2
                    x += 1

        return width, height, bytes(out)


class ArtTile:
    """Simple representation of an art tile.

    Tests expect the constructor signatures `ArtTile(width, height, data)` or
    `ArtTile(width=..., height=..., data=...)` and a `to_image()` method.
    """

    def __init__(self, width: int, height: int, data: bytes) -> None:
        self.width = width
        self.height = height
        self.data = data

    def to_image(self):
        """Convert raw pixel bytes to a PIL Image.

        Supports RGBA/RGB buffers and common UO 16-bit pixels.
        """
        try:
            return image_from_pixels(self.width, self.height, self.data)
        except Exception as e:
            raise FileParseError("Unsupported pixel data for to_image") from e


class ArtLoader:
    """Minimal ArtLoader stub that exposes interface expected by tests."""

    def __init__(self, path: Path | str) -> None:
        """Initialize with a path (file or folder)."""
        self.path = Path(path)
        self._tiles: Dict[int, ArtTile] = {}
        # Optional file index that tests may patch
        self.file_index = None

    def _parse_tile_bytes(self, data: bytes) -> ArtTile:
        """Parse raw bytes for a single art tile.

        Expected layout: 2 bytes width, 2 bytes height (little-endian), then pixel data.
        Raises `FileParseError` for malformed input.
        """
        if not data or len(data) < 4:
            raise FileParseError("Tile data too short")
        width, height = struct.unpack_from("<HH", data, 0)
        # For MUL art files tests use 2 bytes per pixel (mocked), require at least that much
        pixel_bytes_needed = width * height * 2
        if len(data) - 4 < pixel_bytes_needed:
            raise FileParseError("Insufficient pixel data")
        pixels = data[4:4 + pixel_bytes_needed]
        return ArtTile(width, height, pixels)

    def load_tile(self, tile_id: int) -> Optional[ArtTile]:
        """Load a tile.

        Requires `self.file_index` to be set (tests patch it, or callers can
        provide one). This method no longer returns implicit fallback tiles.
        """
        # Return cached if present
        if tile_id in self._tiles:
            return self._tiles[tile_id]

        if not self.file_index:
            raise FileParseError("No file index available")

        return self.load_tile_by_id(tile_id)

    def load_tile_by_id(self, tile_id: int) -> Optional[ArtTile]:
        """Load a tile using an index entry from `self.file_index`.

        Tests patch `file_index.get_entry` and `builtins.open`, so this method
        should read `length` bytes from the underlying file and parse them.
        """
        if not self.file_index:
            raise FileParseError("No file index available")

        entry = self.file_index.get_entry(tile_id)
        try:
            with open(self.path, "rb") as f:
                f.seek(entry.offset)
                data = f.read(entry.length)
        except Exception as e:
            raise FileParseError("Unable to read tile data") from e

        tile = self._parse_tile_bytes(data)
        self._tiles[tile_id] = tile
        return tile
