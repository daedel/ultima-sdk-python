"""
Light module - Manages light source data.
"""

from pathlib import Path
from typing import Optional, List
from .files import Files
from .exceptions import FileAccessException

import math
import struct

from .exceptions import FileParseError
from .file_index import FileIndex
from .rendering import image_from_pixels


class LightData:
    """Represents light source information."""

    def __init__(self, light_id: int, width: int, height: int, pixels: bytes):
        self.light_id = light_id
        self.width = width
        self.height = height
        self.pixels = pixels

    def to_image(self):
        """Convert this light texture to a Pillow image.

        Real client files commonly store either:
        - UO16 5-5-5 pixels (2 bytes/pixel), or
        - 8-bit intensity (1 byte/pixel).

        For 8-bit intensity we render as white with alpha=intensity.
        """
        expected_uo16 = self.width * self.height * 2
        expected_i8 = self.width * self.height

        if len(self.pixels) == expected_uo16:
            return image_from_pixels(
                self.width, self.height, self.pixels, format_hint="UO16"
            )

        if len(self.pixels) == expected_i8:
            rgba = bytearray(self.width * self.height * 4)
            j = 0
            for intensity in self.pixels:
                rgba[j] = 0xFF
                rgba[j + 1] = 0xFF
                rgba[j + 2] = 0xFF
                rgba[j + 3] = intensity
                j += 4
            return image_from_pixels(
                self.width, self.height, bytes(rgba), format_hint="RGBA"
            )

        raise FileParseError("Unsupported light pixel buffer length")


class Light:
    """Static class for managing light data."""

    _index: Optional[FileIndex] = None
    _lights: List[Optional[LightData]] = []
    _initialized = False

    @classmethod
    def initialize(
        cls, idx_path: str | None = None, mul_path: str | None = None
    ) -> bool:
        """Initialize light data."""
        if cls._initialized:
            return True

        try:
            if idx_path is None:
                idx_path = Files.get_file_path("lightidx.mul")
            if mul_path is None:
                mul_path = Files.get_file_path("light.mul")

            if idx_path and mul_path:
                cls._load_lights(idx_path, mul_path)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize light: {e}")

        return False

    @classmethod
    def _load_lights(cls, idx_path: str, mul_path: str) -> None:
        """Load light index and prepare cache."""
        cls._index = FileIndex(idx_path, mul_path)
        # Pre-size cache to number of entries.
        cls._lights = [None] * len(cls._index.entries)

    @staticmethod
    def _decode_light(data: bytes) -> tuple[int, int, bytes]:
        """Decode a single light entry.

        The client file formats vary; we infer width/height from either:
        - a small fixture header: uint16 width, uint16 height, followed by pixels, or
        - known square sizes based on byte length.
        """
        # Fixture layout: <HH width,height then pixels (1 or 2 bytes per pixel)
        # NOTE: Light masks are typically circular and fit within 512x512 max.
        if len(data) >= 4:
            w, h = struct.unpack_from("<HH", data, 0)
            if w > 0 and h > 0 and w <= 512 and h <= 512:
                rest = data[4:]
                if len(rest) in (w * h, w * h * 2):
                    return w, h, rest

        # Infer square sizes.
        def infer_square(n: int) -> Optional[int]:
            if n <= 0:
                return None
            s = int(math.isqrt(n))
            if s * s == n:
                return s
            return None

        # 8-bit intensity
        s = infer_square(len(data))
        if s is not None:
            return s, s, data

        # 16-bit UO pixels
        if len(data) % 2 == 0:
            s2 = infer_square(len(data) // 2)
            if s2 is not None:
                return s2, s2, data

        raise FileParseError("Unsupported light data format")

    @classmethod
    def get_light(cls, light_id: int) -> Optional[LightData]:
        """Get light data by ID."""
        if not cls._initialized:
            cls.initialize()

        if not cls._index:
            return None

        if light_id < 0 or light_id >= len(cls._index.entries):
            return None

        cached = cls._lights[light_id] if light_id < len(cls._lights) else None
        if cached is not None:
            return cached

        try:
            raw = cls._index.read_raw(light_id) if cls._index else None
            if not raw:
                return None
            w, h, pixels = cls._decode_light(raw)
            light = LightData(light_id=light_id, width=w, height=h, pixels=pixels)
            cls._lights[light_id] = light
            return light
        except Exception:
            return None

    @classmethod
    def save_png(cls, light_id: int, path) -> bool:
        """Save a light texture as a PNG.

        Returns True if the light existed and was saved; False if missing.
        """
        try:
            out_path = Path(path)
        except Exception as e:
            raise FileAccessException(f"Invalid output path: {e}")

        light = cls.get_light(int(light_id))
        if light is None:
            return False

        try:
            img = light.to_image()
            img.save(str(out_path), format="PNG")
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to save light PNG: {e}")
