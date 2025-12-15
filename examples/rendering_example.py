"""rendering.py example (synthetic, no client files required).

Creates a small UO16 (5-5-5) gradient buffer and writes it to PNG if Pillow is
installed, otherwise PPM.

Run:
  python -m examples.rendering_example --out out
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
    out_path = Path(out_dir) / "rendering_gradient.png"

    w, h = 96, 48
    buf = bytearray(w * h * 2)
    for y in range(h):
        for x in range(w):
            r = (x * 31) // (w - 1)
            g = (y * 31) // (h - 1)
            b = 31 - ((x * 31) // (w - 1))
            struct.pack_into("<H", buf, (y * w + x) * 2, _rgb555(r, g, b))

    saved = save_uo16_image(w, h, bytes(buf), out_path)
    print(f"Wrote {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
