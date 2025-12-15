"""Gumps example.

Tries to decode a gump and write it as PNG.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.gumps import Gumps

from ._common import add_out_arg, add_uo_root_arg, ensure_out_dir, init_files, resolve_uo_root, save_uo16_image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    add_out_arg(parser)
    parser.add_argument("--id", type=lambda s: int(s, 0), default=0, help="Gump id (default: 0)")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Gumps.initialize()

    candidates = [int(args.id)] + list(range(0, 2000))
    for gump_id in candidates:
        try:
            g = Gumps.get_gump(gump_id)
            if g is None:
                continue
            out_path = Path(out_dir) / f"gump_{gump_id:05d}.png"
            saved = save_uo16_image(g.width, g.height, g.pixels, out_path)
            print(f"Decoded gump {gump_id} -> {saved} ({g.width}x{g.height})")
            return 0
        except Exception:
            continue

    print("Could not decode any gump in 0..1999.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
