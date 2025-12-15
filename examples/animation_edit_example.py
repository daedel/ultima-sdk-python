"""animation_edit.py example (synthetic, no client files required).

Builds a fake AnimationFrame and converts it to an image.
Writes PNG if Pillow is installed, otherwise PPM.

Run:
  python -m examples.animation_edit_example --out out
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

from ultima_sdk.animations import AnimationFrame
from ultima_sdk.animation_edit import AnimationEdit

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
    out_path = Path(out_dir) / "animation_edit_frame.png"

    w, h = 64, 32
    pixels = bytearray(w * h * 2)
    for y in range(h):
        for x in range(w):
            # simple pattern
            r = (x * 31) // (w - 1)
            g = (y * 31) // (h - 1)
            b = 31 if (x // 8) % 2 == 0 else 0
            struct.pack_into("<H", pixels, (y * w + x) * 2, _rgb555(r, g, b))

    frame = AnimationFrame(width=w, height=h, pixels=bytes(pixels))

    # Prefer using AnimationEdit API (requires Pillow), but provide a fallback.
    try:
        img = AnimationEdit.frame_to_image(frame)
        img.save(str(out_path), format="PNG")
        print(f"Wrote {out_path}")
    except ImportError:
        saved = save_uo16_image(w, h, frame.pixels, out_path)
        print(f"Pillow not installed; wrote {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
