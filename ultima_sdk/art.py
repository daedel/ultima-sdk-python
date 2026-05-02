"""ultima_sdk.art

Manages static item art AND land tile art.
"""

from pathlib import Path
from typing import Dict, Optional, Protocol, runtime_checkable
import struct

from .exceptions import FileAccessException, FileParseError
from .files import Files
from .rendering import image_from_pixels

# Land tiles are IDs 0x0000–0x3FFF (16384 IDs).
# Static item art starts at 0x4000.
_LAND_TILE_MAX_ID = 0x3FFF
_LAND_TILE_SIZE = 44
# Diamond format: 44 scanlines, widths 2,6,10,...,44,...,10,6,2
# Total pixels = 1156, raw bytes = 1156 * 2 = 2312
_LAND_TILE_RAW_BYTES = 2312
_LAND_WIDTHS = list(range(2, 46, 4)) + list(range(42, 0, -4))  # 44 rows


@runtime_checkable
class _ArtIndexLike(Protocol):
    def read_raw(self, index: int) -> Optional[bytes]: ...


class ArtData:
    """Represents a single art tile (land or static)."""

    def __init__(self, graphic_id: int, width: int, height: int, pixels: bytes):
        self.graphic_id = graphic_id
        self.width = width
        self.height = height
        self.pixels = pixels  # UO 16-bit BGR-555, row-major, width*height*2 bytes

    def to_image(self):
        return image_from_pixels(self.width, self.height, self.pixels)


class Art:
    """Static class for managing art data."""

    _index: Optional[_ArtIndexLike] = None
    _initialized = False

    @classmethod
    def initialize(
        cls, idx_path: str | None = None, mul_path: str | None = None
    ) -> bool:
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
        """Return art for *graphic_id*.

        IDs 0x0000–0x3FFF → land tile diamond decoder.
        IDs 0x4000+        → static item RLE decoder.
        """
        if not cls._initialized:
            cls.initialize()
        if not cls._index:
            return None

        raw = cls._index.read_raw(graphic_id)
        if not raw:
            return None

        if graphic_id <= _LAND_TILE_MAX_ID:
            return cls._decode_land_tile(graphic_id, raw)
        return cls._decode_static(graphic_id, raw)

    # ------------------------------------------------------------------
    # Land tile decoder
    # ------------------------------------------------------------------

    @classmethod
    def _decode_land_tile(cls, graphic_id: int, data: bytes) -> ArtData:
        """Decode a 44×44 diamond land tile.

        art.mul raw format: NO header — just 1156 tightly-packed uint16 pixels
        in the diamond scanline order (widths 2,6,10,...,44,...,10,6,2).

        UOP sources may deliver a pre-expanded 44×44 square (3872 bytes), which
        is passed through unchanged.
        """
        # UOP: full square already decoded
        if len(data) == _LAND_TILE_SIZE * _LAND_TILE_SIZE * 2:
            return ArtData(graphic_id, _LAND_TILE_SIZE, _LAND_TILE_SIZE, data)

        if len(data) < _LAND_TILE_RAW_BYTES:
            raise FileParseError(
                f"Land tile {graphic_id}: expected >= {_LAND_TILE_RAW_BYTES} bytes, "
                f"got {len(data)}"
            )

        # Expand diamond into a transparent 44×44 canvas (zero = transparent black)
        out = bytearray(_LAND_TILE_SIZE * _LAND_TILE_SIZE * 2)
        src = 0

        for y, row_width in enumerate(_LAND_WIDTHS):
            x_start = (_LAND_TILE_SIZE - row_width) // 2
            for x in range(row_width):
                pixel = struct.unpack_from("<H", data, src)[0]
                src += 2
                dst = (y * _LAND_TILE_SIZE + x_start + x) * 2
                out[dst : dst + 2] = struct.pack("<H", pixel)

        return ArtData(graphic_id, _LAND_TILE_SIZE, _LAND_TILE_SIZE, bytes(out))

    # ------------------------------------------------------------------
    # Static art decoder
    # ------------------------------------------------------------------

    @classmethod
    def _decode_static(cls, graphic_id: int, data: bytes) -> ArtData:
        try:
            width, height, pixels = cls._decode_static_art(data)
            return ArtData(
                graphic_id=graphic_id, width=width, height=height, pixels=pixels
            )
        except FileParseError:
            raise
        except Exception as e:
            raise FileParseError(f"Static art {graphic_id}: {e}") from e

    @classmethod
    def get_equipped_art(
        cls, item_id: int, *, body_id: int | None = None
    ) -> Optional[ArtData]:
        try:
            from .equipconv import EquipConv

            converted = EquipConv.convert(int(item_id), body_id=body_id)
        except Exception:
            converted = int(item_id)
        return cls.get_art(int(converted))

    @classmethod
    def save_png(cls, graphic_id: int, path, *, body_id: int | None = None) -> bool:
        try:
            out_path = Path(path)
        except Exception as e:
            raise FileAccessException(f"Invalid output path: {e}")

        data = (
            cls.get_equipped_art(int(graphic_id), body_id=body_id)
            if body_id is not None
            else cls.get_art(int(graphic_id))
        )
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
        """Decode a static art entry from art.mul.

        Header layout (8 bytes):
          uint16  unknown  (often 0 or non-zero sentinel)
          uint16  unknown
          uint16  width
          uint16  height

        Followed by:
          height * uint16  row lookup offsets (word offsets into run-data stream)
          run-length encoded scanlines:
            each packet: uint16 x_offset, uint16 run_length, run_length * uint16 pixels
            scanline terminates on (0, 0) sentinel
        """
        if len(data) < 8:
            raise FileParseError("Static art data too short")

        _unk0, _unk1, width, height = struct.unpack_from("<HHHH", data, 0)
        if width <= 0 or height <= 0 or width > 4096 or height > 4096:
            raise FileParseError(f"Invalid static art dimensions {width}x{height}")

        lookup_base = 8
        if len(data) < lookup_base + height * 2:
            raise FileParseError("Static art missing lookup table")

        lookups = struct.unpack_from(f"<{height}H", data, lookup_base)
        run_base = lookup_base + height * 2

        out = bytearray(width * height * 2)

        for y in range(height):
            pos = run_base + lookups[y] * 2  # word offset → byte offset
            x = 0
            while pos + 4 <= len(data):
                xoff, run = struct.unpack_from("<HH", data, pos)
                pos += 4
                if xoff == 0 and run == 0:
                    break
                x += xoff
                for _ in range(run):
                    if pos + 2 > len(data):
                        break
                    if 0 <= x < width:
                        dst = (y * width + x) * 2
                        out[dst : dst + 2] = data[pos : pos + 2]
                    pos += 2
                    x += 1

        return width, height, bytes(out)


# ---------------------------------------------------------------------------
# ArtTile / ArtLoader (kept for test compatibility)
# ---------------------------------------------------------------------------


class ArtTile:
    def __init__(self, width: int, height: int, data: bytes) -> None:
        self.width = width
        self.height = height
        self.data = data

    def to_image(self):
        try:
            return image_from_pixels(self.width, self.height, self.data)
        except Exception as e:
            raise FileParseError("Unsupported pixel data for to_image") from e


class ArtLoader:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._tiles: Dict[int, ArtTile] = {}
        self.file_index = None

    def _parse_tile_bytes(self, data: bytes) -> ArtTile:
        if not data or len(data) < 4:
            raise FileParseError("Tile data too short")
        width, height = struct.unpack_from("<HH", data, 0)
        needed = width * height * 2
        if len(data) - 4 < needed:
            raise FileParseError("Insufficient pixel data")
        return ArtTile(width, height, data[4 : 4 + needed])

    def load_tile(self, tile_id: int) -> Optional[ArtTile]:
        if tile_id in self._tiles:
            return self._tiles[tile_id]
        if not self.file_index:
            raise FileParseError("No file index available")
        return self.load_tile_by_id(tile_id)

    def load_tile_by_id(self, tile_id: int) -> Optional[ArtTile]:
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
