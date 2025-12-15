"""Art example.

Tries to decode a static art tile and write it as PNG.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.art import Art

from ._common import add_out_arg, add_uo_root_arg, ensure_out_dir, init_files, resolve_uo_root, save_uo16_image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    add_out_arg(parser)
    parser.add_argument("--id", type=lambda s: int(s, 0), default=0x4000, help="Art id (default: 0x4000)")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Art.initialize()

    # Try requested id, then fall back to a small range.
    candidates = [int(args.id)] + list(range(0x4000, 0x4020))
    for art_id in candidates:
        try:
            a = Art.get_art(art_id)
            if a is None:
                continue
            out_path = Path(out_dir) / f"art_{art_id:05X}.png"
            saved = save_uo16_image(a.width, a.height, a.pixels, out_path)
            print(f"Decoded art 0x{art_id:X} -> {saved} ({a.width}x{a.height})")
            return 0
        except Exception:
            continue

    print("Could not decode any art tile in the tested range.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
