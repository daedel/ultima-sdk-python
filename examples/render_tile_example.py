"""Rendering example.

Writes a small PNG using the built-in Pillow rendering helpers.

Run:
  python -m examples.render_tile_example
"""

from __future__ import annotations

import struct
from pathlib import Path

from ._common import add_out_arg, ensure_out_dir, save_uo16_image


def _rgb555(r: int, g: int, b: int) -> int:
    r5 = max(0, min(31, r))
    g5 = max(0, min(31, g))
    b5 = max(0, min(31, b))
    return (r5 << 10) | (g5 << 5) | b5


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    add_out_arg(parser)
    args = parser.parse_args()

    out_dir = ensure_out_dir(args.out)
    out_path = Path(out_dir) / "render_tile.png"

    w, h = 64, 64
    buf = bytearray(w * h * 2)
    for y in range(h):
        for x in range(w):
            r = (x * 31) // (w - 1)
            g = (y * 31) // (h - 1)
            b = ((x + y) * 31) // (w + h - 2)
            pix = _rgb555(r, g, b)
            struct.pack_into("<H", buf, (y * w + x) * 2, pix)

    saved = save_uo16_image(w, h, bytes(buf), out_path)
    print(f"Wrote {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
