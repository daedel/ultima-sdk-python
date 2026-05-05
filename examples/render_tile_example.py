"""Render tile example.

Writes a synthetic UO16 image using the SDK rendering helpers.
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

from ._common import add_out_arg, ensure_out_dir, save_uo16_image


def _rgb555(r: int, g: int, b: int) -> int:
    r5 = max(0, min(31, r))
    g5 = max(0, min(31, g))
    b5 = max(0, min(31, b))
    return (r5 << 10) | (g5 << 5) | b5


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_out_arg(parser)
    args = parser.parse_args()

    out_dir = ensure_out_dir(args.out)
    out_path = Path(out_dir) / "render_tile.png"

    width, height = 64, 64
    pixels = bytearray(width * height * 2)
    for y in range(height):
        for x in range(width):
            r = (x * 31) // (width - 1)
            g = (y * 31) // (height - 1)
            b = ((x + y) * 31) // (width + height - 2)
            struct.pack_into("<H", pixels, (y * width + x) * 2, _rgb555(r, g, b))

    saved = save_uo16_image(width, height, bytes(pixels), out_path)
    print(f"Wrote {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
