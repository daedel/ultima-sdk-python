""" Art module - Reads land tile and static item art from artidx.mul / art.mul
(or art.uop for High Seas clients).

Land tile geometry:
     44 rows arranged as an isometric diamond:
     top half:    row widths 2, 4, 6, ..., 44 (22 rows, step +2)
     bottom half: row widths 44, 42, ..., 2   (22 rows, step -2)
     Each row is left-padded so the diamond is centred in a 44x44 bounding box.
     Pixel values read directly from the stream, ORed with 0x8000 (opaque bit).

Static art (MUL format):
     4-byte header (ignored), then <HH width height>, then RLE.

Static art (UOP format):
     Payload starts directly with <HH width height> followed by raw pixels.
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

    Supports both tuple unpacking (pixels, width, height = tile) for backward
    compatibility and attribute access (tile.width, tile.height) for new code.
    Also provides to_image() for save_png() integration.
    """

    pixels: List[List[int]]
    width: int
    height: int

    def to_image(self):
        """Convert pixel data to a PIL Image (RGBA)."""
        from PIL import Image

        img = Image.new("RGBA", (self.width, self.height))
        pix = img.load()
        for y, row in enumerate(self.pixels):
            for x, color in enumerate(row):
                if color:
                    r = ((color >> 10) & 0x1F) << 3
                    g = ((color >> 5) & 0x1F) << 3
                    b = (color & 0x1F) << 3
                    pix[x, y] = (r, g, b, 255)
        return img


class Art:
    """Static class for loading art tiles."""

    _index: Optional[object] = None
    _initialized: bool = False

    # Pre-computed land-tile row widths: 44 rows, diamond shape, step 2.
    # Top half: 2, 4, ..., 44 (indices 0-21)
    # Bottom half: 44, 42, ..., 2 (indices 22-43)
    LAND_ROW_WIDTHS: List[int] = (
        list(range(2, 46, 2))  # 2..44 -- 22 values
        + list(range(44, 0, -2))  # 44..2 -- 22 values
    )  # total 44 values; max = 44

    # Overlay cache: maps mul-file id (land=id, static=id+0x4000) -> raw bytes.
    # Populated by apply_verdata_patch(); checked before hitting _index.
    _patch_cache: dict = {}

    @classmethod
    def initialize(
        cls, idx_path: Optional[str] = None, mul_path: Optional[str] = None
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
        """Backward compatibility alias."""
        if id >= 0x4000:
            return cls.get_static_tile(id - 0x4000)
        return cls.get_land_tile(id)  # type: ignore[return-value]

    @classmethod
    def get_equipped_art(cls, id: int, body_id: int = None) -> Optional[ArtTile]:
        """Backward compatibility alias for equipconv tests."""
        return cls.get_art(id)

    @classmethod
    def save_png(
        cls, id: int, path: str | Path, *, body_id: Optional[int] = None
    ) -> bool:
        """Render art to PNG file.

        Uses get_equipped_art() when body_id is supplied, get_art() otherwise.
        The returned data object must support .to_image() -> PIL Image.
        """
        try:
            if body_id is not None:
                data = cls.get_equipped_art(id, body_id=body_id)
            else:
                data = cls.get_art(id)
            if data is None:
                return False
            img = data.to_image()
            img.save(path, "PNG")
            return True
        except Exception:
            return False

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

        ArtTile is a NamedTuple so both tuple unpacking and attribute access work:
            pixels, width, height = tile  # backward compat
            tile.width                    # new code / UOP fallback tests

        MUL format: data starts with 4 ignored bytes, then <HH w h>, then RLE.
        UOP format: data starts directly with <HH w h> followed by raw pixels.
        """
        if not cls._initialized:
            cls.initialize()
        data = cls._get_raw_data(id + 0x4000)
        if data is None or len(data) < 4:
            return None

        if cls._is_uop():
            return cls._decode_uop_static(data)
        else:
            return cls._decode_mul_static(data)

    @classmethod
    def _decode_uop_static(cls, data: bytes) -> Optional[ArtTile]:
        """Decode UOP static art payload: <HH w h> + raw pixels (row-major)."""
        if len(data) < 4:
            return None
        width, height = struct.unpack_from("<HH", data, 0)
        if width == 0 or height == 0:
            return None
        pixel_bytes = data[4:]
        pixels: List[List[int]] = []
        for y in range(height):
            row: List[int] = []
            for x in range(width):
                offset = (y * width + x) * 2
                if offset + 2 > len(pixel_bytes):
                    row.append(0)
                else:
                    (color,) = struct.unpack_from("<H", pixel_bytes, offset)
                    if color != 0:
                        color |= 0x8000
                    row.append(color)
            pixels.append(row)
        return ArtTile(pixels=pixels, width=width, height=height)

    @classmethod
    def _decode_mul_static(cls, data: bytes) -> Optional[ArtTile]:
        """Decode MUL static art payload: 4 ignored bytes, <HH w h>, RLE."""
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
        pixels: List[List[int]] = []
        for y in range(height):
            row: List[int] = [0] * width
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
                    row[x] = pixel
                    x += 1
            pixels.append(row)
        return ArtTile(pixels=pixels, width=width, height=height)

    @classmethod
    def apply_verdata_patch(
        cls, block_id: int, data: bytes, extra: Optional[int] = None
    ) -> None:
        if not cls._initialized:
            cls.initialize()
        cls._patch_cache[block_id] = data
        if extra:
            cls._patch_cache[(block_id, "extra")] = extra
