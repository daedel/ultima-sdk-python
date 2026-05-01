"""Rendering helpers.

This module provides small, dependency-light helpers for converting common
Ultima Online pixel encodings into Pillow images.

Notes:
- Many UO assets use 16-bit 5-5-5 color. This module provides a pragmatic
  conversion for previewing and basic tooling.
- Hue application and format-specific decoding (RLE, indexed palettes, etc.)
  are intentionally out of scope here.
"""

from __future__ import annotations

from typing import Literal, Optional, TYPE_CHECKING

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore

if TYPE_CHECKING:  # pragma: no cover
    from PIL import Image as PILImage


def _require_pillow():
    if Image is None:  # pragma: no cover
        raise ImportError(
            "Pillow is required for image rendering. Install with `pip install pillow`."
        )


def uo_16bit_555_to_rgba(pixels: bytes, *, transparent_zero: bool = True) -> bytes:
    """Convert little-endian 16-bit 5-5-5 pixels to RGBA bytes.

    Args:
        pixels: Raw 16-bit pixel bytes (little-endian, 2 bytes per pixel).
        transparent_zero: If True, treat value 0 as fully transparent.

    Returns:
        RGBA bytes (4 bytes per pixel).

    Raises:
        ValueError: If the input length is not even.
    """
    if len(pixels) % 2 != 0:
        raise ValueError("16-bit pixel buffer length must be even")

    out = bytearray((len(pixels) // 2) * 4)

    # Use struct.iter_unpack to respect little-endian.
    import struct

    i = 0
    for (value,) in struct.iter_unpack("<H", pixels):
        if transparent_zero and value == 0:
            out[i : i + 4] = b"\x00\x00\x00\x00"
            i += 4
            continue

        r5 = (value >> 10) & 0x1F
        g5 = (value >> 5) & 0x1F
        b5 = value & 0x1F

        r = (r5 << 3) | (r5 >> 2)
        g = (g5 << 3) | (g5 >> 2)
        b = (b5 << 3) | (b5 >> 2)

        out[i] = r
        out[i + 1] = g
        out[i + 2] = b
        out[i + 3] = 0xFF
        i += 4

    return bytes(out)


def image_from_pixels(
    width: int,
    height: int,
    pixels: bytes,
    *,
    format_hint: Optional[Literal["RGBA", "RGB", "UO16"]] = None,
) -> "PILImage.Image":
    """Create a Pillow image from raw pixel bytes.

    Supported input formats:
    - RGBA: 4 bytes per pixel
    - RGB: 3 bytes per pixel
    - UO16: 2 bytes per pixel (16-bit 5-5-5)

    Args:
        width: Image width.
        height: Image height.
        pixels: Raw pixel bytes.
        format_hint: Optionally force a format.

    Raises:
        ImportError: If Pillow is not installed.
        ValueError: If pixel length doesn't match width/height.
    """
    _require_pillow()
    assert Image is not None

    expected_rgba = width * height * 4
    expected_rgb = width * height * 3
    expected_uo16 = width * height * 2

    if format_hint == "RGBA" or (format_hint is None and len(pixels) == expected_rgba):
        if len(pixels) != expected_rgba:
            raise ValueError("Pixel data length does not match RGBA dimensions")
        return Image.frombytes("RGBA", (width, height), pixels)

    if format_hint == "RGB" or (format_hint is None and len(pixels) == expected_rgb):
        if len(pixels) != expected_rgb:
            raise ValueError("Pixel data length does not match RGB dimensions")
        return Image.frombytes("RGB", (width, height), pixels)

    if format_hint == "UO16" or (format_hint is None and len(pixels) == expected_uo16):
        if len(pixels) != expected_uo16:
            raise ValueError("Pixel data length does not match 16-bit dimensions")
        rgba = uo_16bit_555_to_rgba(pixels, transparent_zero=True)
        return Image.frombytes("RGBA", (width, height), rgba)

    raise ValueError(
        "Unsupported pixel buffer length; expected RGB/RGBA/16-bit UO pixels for given dimensions"
    )
