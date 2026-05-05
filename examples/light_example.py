"""Light example.

Loads a light source from light.mul and writes it as an image.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.light import Light

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
    parser.add_argument("--id", type=int, default=0, help="Light id")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Light.initialize()
    out_path = Path(out_dir) / f"light_{int(args.id):04d}.png"

    if Light.save_png(int(args.id), out_path):
        print(f"Wrote {out_path}")
        return 0

    print(f"Light id {args.id} not found")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
