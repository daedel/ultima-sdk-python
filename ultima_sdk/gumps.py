""" Gumps module - Reads gump images from gumpart.mul / gumpart.idx.

MUL/IDX format (each row):
        Lookup table: height ushort values, each is a ushort-array index into the
                      RLE data (multiply by 2 to get byte offset from data start).
        RLE stream:   pairs of (color: ushort, run: ushort) -- color FIRST per C# ref.

        Width and height come from the INDEX extra field, NOT from the data block.
            extra >> 16 & 0xFFFF = width
            extra & 0xFFFF       = height

Raw / test format (extra == 0):
        Payload starts directly with <HH width height> followed by
        width*height*2 raw 16-bit pixel bytes (row-major, no RLE).

UOP format (gumpartlegacymul.uop with has_extra=True):
        After stripping the 8-byte prefix (handled by UopFile.read_raw),
        the payload begins with struct.pack("<HH", width, height) followed
        by raw 16-bit pixel data (row-major, no lookup table, no RLE).

Every non-zero color must have bit 15 (0x8000) set for the display layer
to treat it as opaque (15-bit RGB, bit-15 = opacity).
"""
import struct
from typing import Optional, List, NamedTuple
from pathlib import Path
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException


class GumpImage(NamedTuple):
    """Result object returned by get_gump.

    pixels: raw bytes (width * height * 2 bytes of 16-bit LE colours).
    Supports both tuple unpacking (pixels, width, height = g) for backward
    compatibility and attribute access (g.width, g.height) for new code.
    Also provides to_image() for save_png() integration.
    """

    pixels: bytes
    width: int
    height: int

    def to_image(self):
        """Convert pixel data to a PIL Image (RGBA)."""
        from PIL import Image
        img = Image.new("RGBA", (self.width, self.height))
        pix = img.load()
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
        return img


class Gumps:
    """Static class for loading gump images."""

    _index: Optional[object] = None
    _initialized: bool = False

    # Overlay cache: maps gump id -> (raw_bytes, extra) from verdata patches.
    _patch_cache: dict = {}

    @classmethod
    def initialize(
        cls,
        idx_path: Optional[str] = None,
        mul_path: Optional[str] = None
    ) -> bool:
        """Initialize Gumps static state.

        Tries MUL files first; if unavailable falls back to gumpartlegacymul.uop.
        Optionally accepts explicit paths for testing.
        """
        if cls._initialized and not idx_path and not mul_path:
            return True

        # --- MUL path ---
        try:
            resolved_idx = idx_path or Files.get_file_path("gumpidx.mul")
            resolved_mul = mul_path or Files.get_file_path("gumpart.mul")
            if resolved_idx and resolved_mul:
                cls._index = FileIndex(resolved_idx, resolved_mul, entry_size=12)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize Gumps: {e}")

        # --- UOP fallback ---
        try:
            from .uop import UopBackedIndex
            uop_path = Files.get_file_path("gumpartlegacymul.uop")
            if uop_path:
                cls._index = UopBackedIndex(
                    uop_path,
                    "build/gumpartlegacymul/{0:D8}.tga",
                    has_extra=True,
                )
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize Gumps via UOP: {e}")

        return False

    @classmethod
    def save_png(cls, id: int, path: str | Path) -> bool:
        """Render gump to PNG file.

        The returned data object must support .to_image() -> PIL Image.
        Raises exceptions for invalid paths or other I/O errors.
        """
                try:
            out_path = Path(path)
        except Exception as e:
            raise FileAccessException(f"Invalid output path: {e}")
        data = cls.get_gump(id)
        if data is None:
            return False
        img = data.to_image()
        img.save(path, "PNG")
        return True

    @classmethod
    def get_gump(cls, id: int) -> Optional[GumpImage]:
        """Return GumpImage for gump *id*, or None.

        GumpImage is a NamedTuple so both tuple unpacking and attribute access work.
        GumpImage.pixels is raw bytes (width * height * 2 bytes).
        """
        if not cls._initialized:
            cls.initialize()

        # Check verdata patch cache first.
        if id in cls._patch_cache:
            data, extra = cls._patch_cache[id]
            width = (extra >> 16) & 0xFFFF
            height = extra & 0xFFFF
            if width == 0 and height == 0:
                return cls._decode_raw_gump(data)
            return cls._decode_mul_rle(data, width, height)

        if cls._index is None:
            return None

        # Detect UOP path vs MUL/IDX path.
        from .uop import UopBackedIndex
        if isinstance(cls._index, UopBackedIndex):
            return cls._decode_uop_gump(id)
        else:
            result = cls._index.read_raw_with_extra(id)
            if result is None:
                return None
            data, extra = result
            width = (extra >> 16) & 0xFFFF
            height = extra & 0xFFFF
            # When extra == 0 (raw/test format), read w/h from data payload.
            if width == 0 and height == 0:
                return cls._decode_raw_gump(data)
            return cls._decode_mul_rle(data, width, height)

    @classmethod
    def _decode_raw_gump(cls, data: bytes) -> Optional[GumpImage]:
        """Decode raw/test-format gump: <HH w h> + w*h*2 raw pixel bytes."""
        if len(data) < 4:
            return None
        width, height = struct.unpack_from("<HH", data, 0)
        if width == 0 or height == 0:
            return None
        pixel_bytes = data[4:4 + width * height * 2]
        return GumpImage(pixels=pixel_bytes, width=width, height=height)

    @classmethod
    def _decode_uop_gump(cls, id: int) -> Optional[GumpImage]:
        """Decode a gump from UOP storage.

        After the UopFile strips the 8-byte has_extra prefix, the remaining
        payload starts with struct.pack('<HH', width, height) followed by raw
        width*height*2 pixel bytes.
        """
        if cls._index is None:
            return None
        data = cls._index.read_raw(id)
        if data is None or len(data) < 4:
            return None
        width, height = struct.unpack_from("<HH", data, 0)
        if width == 0 or height == 0:
            return None
        pixel_bytes = data[4:4 + width * height * 2]
        return GumpImage(pixels=pixel_bytes, width=width, height=height)

    @classmethod
    def _decode_mul_rle(cls, data: bytes, width: int, height: int) -> Optional[GumpImage]:
        """Decode MUL-format RLE gump data into a GumpImage.

        Returns GumpImage with pixels as raw bytes (width*height*2).
        """
        if width == 0 or height == 0:
            return None
        lookup_count = height
        lookup_bytes = lookup_count * 2
        if len(data) < lookup_bytes:
            return None
        lookups = struct.unpack_from(f"<{lookup_count}H", data, 0)
        out = bytearray(width * height * 2)
        for y in range(height):
            row_byte_offset = lookups[y] * 2
            pos = row_byte_offset
            cur_x = 0
            while cur_x < width:
                if pos + 4 > len(data):
                    break
                color, run = struct.unpack_from("<HH", data, pos)
                pos += 4
                if color:
                    color |= 0x8000
                for _ in range(run):
                    if cur_x >= width:
                        break
                    out_idx = (y * width + cur_x) * 2
                    struct.pack_into("<H", out, out_idx, color)
                    cur_x += 1
        return GumpImage(pixels=bytes(out), width=width, height=height)

    @classmethod
    def apply_verdata_patch(cls, block_id: int, data: bytes, extra: int) -> None:
        """Cache raw verdata patch bytes for a gump."""
        if not cls._initialized:
            cls.initialize()
        cls._patch_cache[block_id] = (data, extra)
