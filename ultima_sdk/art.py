""" Art module - Reads land tile and static item art from artidx.mul / art.mul
(or art.uop for High Seas clients).

Land tile geometry:
        44 rows arranged as an isometric diamond:
        top half:    row widths 2, 4, 6, ..., 44 (22 rows, step +2)
        bottom half: row widths 44, 42, ..., 2  (22 rows, step -2)
        Each row is left-padded so the diamond is centred in a 44x44 bounding box.
        Pixel values read directly from the stream, ORed with 0x8000 (opaque bit).

Static art (MUL format):
        4-byte header (ignored), then <HH width height>, then RLE.

Static art (UOP / raw format):
        Payload starts directly with <HH width height> followed by raw
        width*height*2 bytes of 16-bit pixel data (row-major).
        No 4-byte ignored header, no lookup table, no RLE.
"""
import struct
from typing import Optional, List, NamedTuple
from pathlib import Path
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException


class ArtTile(NamedTuple):
    """Result object returned by get_static_tile / get_art.

    pixels: raw bytes (width * height * 2 bytes of 16-bit LE colours).
    Supports both tuple unpacking (pixels, width, height = tile) for backward
    compatibility and attribute access (tile.width, tile.height) for new code.
    Also provides to_image() for save_png() integration.
    """

        pixels: object  # bytes (raw) or List[List[int]] (MUL 2D rows)
    width: int
    height: int

        def to_image(self):
        """Convert pixel data to a PIL Image (RGBA).
        Supports both raw bytes (from _decode_raw_static) and
        2D list of rows (from _decode_mul_static)."""
        from PIL import Image
        img = Image.new("RGBA", (self.width, self.height))
        pix = img.load()
        if isinstance(self.pixels, (bytes, bytearray)):
            # Raw bytes format
            for y in range(self.height):
                for x in range(self.width):
                    offset = (y * self.width + x) * 2
                    if offset + 2 > len(self.pixels):
                        continue
                    (color,) = struct.unpack_from("<H", self.pixels, offset)
                    if color:
                        r = ((color >> 10) & 0x1F) << 3
                        g = ((color >> 5) & 0x1F) << 3
                        b = (color & 0x1F) << 3
                        pix[x, y] = (r, g, b, 255)
        else:
            # 2D list of rows format
            for y in range(self.height):
                for x in range(self.width):
                    color = self.pixels[y][x]
                    if color:
                        r = ((color >> 10) & 0x1F) << 3
                        g = ((color >> 5) & 0x1F) << 3
                        b = (color & 0x1F) << 3
                        pix[x, y] = (r, g, b, 255)
        return img


class EquippedArtTile:
    """Return value from get_equipped_art(); wraps an ArtTile with a resolved graphic_id."""

    def __init__(self, tile: Optional[ArtTile], graphic_id: int):
        self._tile = tile
        self.graphic_id = graphic_id

    def __getattr__(self, name: str):
        return getattr(self._tile, name)

    def __bool__(self) -> bool:
        return self._tile is not None


class Art:
    """Static class for loading art tiles."""

    _index: Optional[object] = None
    _initialized: bool = False

    # Pre-computed land-tile row widths: 44 rows, diamond shape, step 2.
    # Top half: 2, 4, ..., 44 (indices 0-21)
    # Bottom half: 44, 42, ..., 2 (indices 22-43)
    LAND_ROW_WIDTHS: List[int] = (
        list(range(2, 46, 2))   # 2..44 -- 22 values
        + list(range(44, 0, -2))  # 44..2 -- 22 values
    )  # total 44 values; max = 44

    # Overlay cache: maps mul-file id -> raw bytes.
    # For static tiles (MUL path): key = block_id + 0x4000
    # Populated by apply_verdata_patch(); checked before hitting _index.
    _patch_cache: dict = {}

    @classmethod
    def initialize(
        cls,
        idx_path: Optional[str] = None,
        mul_path: Optional[str] = None
    ) -> bool:
        """Initialize Art static state.

        Tries MUL files first; if unavailable falls back to artlegacymul.uop.
        Optionally accepts explicit paths for testing.
        """
        if cls._initialized and not idx_path and not mul_path:
            return True

        # --- MUL path ---
        try:
            resolved_idx = idx_path or Files.get_file_path("artidx.mul")
            resolved_mul = mul_path or Files.get_file_path("art.mul")
            if resolved_idx and resolved_mul:
                cls._index = FileIndex(resolved_idx, resolved_mul, entry_size=12)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize Art: {e}")

        # --- UOP fallback ---
        try:
            from .uop import UopBackedIndex
            uop_path = Files.get_file_path("artlegacymul.uop")
            if uop_path:
                cls._index = UopBackedIndex(
                    uop_path,
                    "build/artlegacymul/{0:D8}.tga",
                    has_extra=False,
                )
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize Art via UOP: {e}")

        return False

    @classmethod
    def _is_uop(cls) -> bool:
        """Return True if the active index is a UOP-backed index."""
        try:
            from .uop import UopBackedIndex
            return isinstance(cls._index, UopBackedIndex)
        except Exception:
            return False

    @classmethod
    def get_art(cls, id: int) -> Optional[ArtTile]:
        """Return ArtTile for the given art id.

        For id >= 0x4000: delegates to get_static_tile(id - 0x4000).
        For id < 0x4000: reads raw data and decodes as a raw/UOP-format tile
        (i.e., <HH width height> followed by raw 16-bit pixels).
        Use get_land_tile() for the land-tile diamond pixel list.
        """
        if id >= 0x4000:
            return cls.get_static_tile(id - 0x4000)
        # Land tile range: decode raw data as raw/UOP-format static art.
        if not cls._initialized:
            cls.initialize()
        data = cls._get_raw_data(id)
        if data is None:
            return None
        return cls._decode_raw_static(data)

    @classmethod
    def get_equipped_art(
        cls, id: int, body_id: Optional[int] = None
    ) -> Optional[EquippedArtTile]:
        """Return EquippedArtTile for art id, applying EquipConv remapping.

        Looks up an EquipConv override for (id, body_id) to find the actual
        graphic id to load.  Returns None if the resolved graphic is missing.
        """
        from .equipconv import EquipConv
        resolved_id = EquipConv.try_convert(id, body_id=body_id)
        if resolved_id is None:
            resolved_id = id
        tile = cls.get_art(resolved_id)
        if tile is None:
            return None
        return EquippedArtTile(tile, graphic_id=resolved_id)

    @classmethod
    def save_png(
        cls, id: int, path: str | Path, *, body_id: Optional[int] = None
    ) -> bool:
        """Render art to PNG file.

        Uses get_equipped_art() when body_id is supplied, get_art() otherwise.
        The returned data object must support .to_image() -> PIL Image.
        Raises exceptions for invalid paths or other I/O errors.
        """
        if body_id is not None:
            data = cls.get_equipped_art(id, body_id=body_id)
        else:
            data = cls.get_art(id)
        if data is None:
            return False
        img = data.to_image()
        img.save(path, "PNG")
        return True

    @classmethod
    def _get_raw_data(cls, mul_id: int) -> Optional[bytes]:
        """Read raw bytes for mul_id, checking the verdata patch cache first."""
        if mul_id in cls._patch_cache:
            return cls._patch_cache[mul_id]
        if cls._index is None:
            return None
        return cls._index.read_raw(mul_id)

    @classmethod
    def get_land_tile(cls, id: int) -> Optional[List[List[int]]]:
        """Return a list of 44 rows (each 44 pixels wide) for land tile *id*.

        Returns the raw pixel list directly for backward compatibility with
        tests that call len(result) or iterate rows directly.
        """
        if not cls._initialized:
            cls.initialize()
        data = cls._get_raw_data(id)
        if data is None:
            return None
        pos = 0
        rows: List[List[int]] = []
        for row_idx, row_width in enumerate(cls.LAND_ROW_WIDTHS):
            left_pad = (44 - row_width) // 2
            row: List[int] = [0] * 44
            for col in range(row_width):
                if pos + 2 > len(data):
                    break
                (pixel,) = struct.unpack_from("<H", data, pos)
                pos += 2
                if pixel != 0:
                    pixel |= 0x8000
                row[left_pad + col] = pixel
            rows.append(row)
        return rows

    @classmethod
    def get_static_tile(cls, id: int) -> Optional[ArtTile]:
        """Return ArtTile(pixels, width, height) for static tile *id*, or None.

        ArtTile.pixels is raw bytes (width * height * 2 bytes of 16-bit LE colours).

        MUL format: data at mul-index (id + 0x4000) starts with 4 ignored bytes,
                    then <HH w h>, then RLE (decoded to raw pixels).
        UOP format: data is looked up directly by id (no 0x4000 offset),
                    starts with <HH w h> followed by raw pixel bytes.
        """
        if not cls._initialized:
            cls.initialize()
        if cls._is_uop():
            data = cls._get_raw_data(id)
        else:
            data = cls._get_raw_data(id + 0x4000)
        if data is None or len(data) < 4:
            return None
        if cls._is_uop():
            return cls._decode_raw_static(data)
        else:
                        return cls._decode_mul_static(data)

    @classmethod
    def _decode_raw_static(cls, data: bytes) -> Optional[ArtTile]:
        """Decode raw/UOP static art: <HH w h> + width*height*2 raw pixel bytes."""
        if len(data) < 4:
            return None
        width, height = struct.unpack_from("<HH", data, 0)
        if width == 0 or height == 0:
            return None
        pixel_bytes = data[4:4 + width * height * 2]
        return ArtTile(pixels=pixel_bytes, width=width, height=height)

    @classmethod
    def _decode_mul_static(cls, data: bytes) -> Optional[ArtTile]:
        """Decode MUL static art payload: 4 ignored bytes, <HH w h>, RLE.

        Decodes the RLE stream into raw flat pixel bytes (width*height*2).
        """
        if len(data) < 8:
            return None
        pos = 4  # skip 4-byte ignored header
        width, height = struct.unpack_from("<HH", data, pos)
        pos += 4
        if width == 0 or height == 0:
            return None
        lookup_bytes = height * 2
        if pos + lookup_bytes > len(data):
            return None
        lookups = struct.unpack_from(f"<{height}H", data, pos)
        pos += lookup_bytes
        pixel_data_start = pos
                rows: List[List[int]] = [[0] * width for _ in range(height)]
        for y in range(height):
            rle_pos = pixel_data_start + lookups[y] * 2
            x = 0
            while x < width:
                if rle_pos + 4 > len(data):
                    break
                offset, run = struct.unpack_from("<HH", data, rle_pos)
                rle_pos += 4
                if offset == 0 and run == 0:
                    break
                x += offset
                for _ in range(run):
                    if rle_pos + 2 > len(data) or x >= width:
                        break
                    (pixel,) = struct.unpack_from("<H", data, rle_pos)
                    rle_pos += 2
                    if pixel != 0:
                        pixel |= 0x8000
                    rows[y][x] = pixel
                                                            x += 1
                return ArtTile(pixels=rows, width=width, height=height)

    @classmethod
    def apply_verdata_patch(cls, block_id: int, data: bytes, extra: int = 0) -> None:
        """Cache raw verdata patch bytes for a static art tile.

        block_id is the static tile index (0 = first static tile).  For the
        MUL lookup path the internal mul-file key is block_id + 0x4000, so we
        store the data under that key so _get_raw_data() can find it.
        """
        if not cls._initialized:
            cls.initialize()
                cls._patch_cache[block_id] = data
                if extra:
            cls._patch_cache[(block_id, "extra")] = extra
