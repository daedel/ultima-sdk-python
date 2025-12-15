"""Hues example.

Prints the first hue entry and writes a small palette PNG.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.hues import Hues

from ._common import add_out_arg, add_uo_root_arg, ensure_out_dir, init_files, resolve_uo_root, save_uo16_image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    add_out_arg(parser)
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True, require_any=("hues.mul",))
    out_dir = ensure_out_dir(args.out)

    Hues.initialize()
    h = Hues.get_hue(0)
    if h is None:
        print("No hue[0]")
        return 1

    print("Hue count:", Hues.count())
    print("Hue[0] first 8 colors (UO16):", [h.get_color(i) for i in range(8)])

    # Render 16 swatches in a row using UO16 pixel values.
    w, h_px = 16 * 16, 16
    pixels = bytearray(w * h_px * 2)
    for i in range(16):
        color = int(h.get_color(i) or 0)
        for y in range(h_px):
            for x in range(16):
                idx = (y * w + (i * 16 + x)) * 2
                pixels[idx:idx + 2] = color.to_bytes(2, "little", signed=False)

    out_path = Path(out_dir) / "hue0_palette.png"
    saved = save_uo16_image(w, h_px, bytes(pixels), out_path)
    print(f"Wrote {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
