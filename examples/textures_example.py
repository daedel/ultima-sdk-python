"""Textures example.

Loads a landscape texture and writes it as an image.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.textures import Textures

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
    parser.add_argument("--id", type=int, default=0, help="Texture id")
    args = parser.parse_args()

    init_files(
        resolve_uo_root(args.uo_root),
        require=True,
        require_any=("texmaps.mul", "texidx.mul"),
    )
    out_dir = ensure_out_dir(args.out)

    Textures.initialize()
    out_path = Path(out_dir) / f"texture_{args.id:04d}.png"

    if Textures.save_png(args.id, out_path):
        print(f"Wrote {out_path}")
        return 0

    print(f"Texture id {args.id} not found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
