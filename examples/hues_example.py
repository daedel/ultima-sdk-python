"""Hues example.

Loads hues.mul, prints the first palette entry, and writes a small palette image.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.hues import Hues

from ._common import (
    add_out_arg,
    add_uo_root_arg,
    ensure_out_dir,
    init_files,
    resolve_uo_root,
    save_uo16_image,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    add_out_arg(parser)
    args = parser.parse_args()

    init_files(
        resolve_uo_root(args.uo_root),
        require=True,
        require_any=("hues.mul",),
    )
    out_dir = ensure_out_dir(args.out)

    Hues.initialize()
    count = Hues.get_count()
    print(f"Hues loaded: {count}")

    hue = Hues.get_hue(0)
    if hue is None:
        print("No hue entry found")
        return 1

    colors = hue["colors"] if isinstance(hue, dict) else []
    print("First 8 hue entries:", [hex(c) for c in colors[:8]])

    width, height = 16 * 16, 16
    pixels = bytearray(width * height * 2)
    for slot in range(16):
        color = colors[slot] if slot < len(colors) else 0
        for y in range(height):
            for x in range(16):
                offset = (y * width + slot * 16 + x) * 2
                pixels[offset : offset + 2] = int(color).to_bytes(2, "little")

    out_path = Path(out_dir) / "hues_palette.png"
    saved = save_uo16_image(width, height, bytes(pixels), out_path)
    print(f"Wrote {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
