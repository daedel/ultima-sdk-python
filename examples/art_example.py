"""Art example.

Loads a static art tile and writes it as an image.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.art import Art

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
    parser.add_argument(
        "--id",
        type=lambda s: int(s, 0),
        default=0x4000,
        help="Static art id (default: 0x4000)",
    )
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Art.initialize()
    art_id = int(args.id)
    out_path = Path(out_dir) / f"art_{art_id:05X}.png"
    if Art.save_png(art_id, out_path):
        print(f"Wrote {out_path}")
        return 0

    print(f"Art id {art_id} not found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
