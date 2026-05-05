"""Gumps example.

Loads a gump image and writes it as a PNG file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.gumps import Gumps

from ._common import (
    add_out_arg,
    add_uo_root_arg,
    ensure_out_dir,
    init_files,
    resolve_uo_root,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    add_out_arg(parser)
    parser.add_argument("--id", type=lambda s: int(s, 0), default=0, help="Gump id")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Gumps.initialize()
    out_path = Path(out_dir) / f"gump_{int(args.id):05d}.png"

    if Gumps.save_png(int(args.id), out_path):
        print(f"Wrote {out_path}")
        return 0

    print(f"Gump id {args.id} not found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
