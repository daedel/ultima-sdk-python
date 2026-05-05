"""TileData example.

Loads tile data and prints a few land and item entries.
"""

from __future__ import annotations

import argparse

from ultima_sdk.tiledata import TileData

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    parser.add_argument("--land-id", type=int, default=0, help="Land tile id")
    parser.add_argument("--item-id", type=int, default=0, help="Item tile id")
    args = parser.parse_args()

    init_files(
        resolve_uo_root(args.uo_root),
        require=True,
        require_any=("tiledata.mul",),
    )

    TileData.initialize()
    land = TileData.get_land_tile(args.land_id)
    item = TileData.get_item_tile(args.item_id)

    print(f"Land tile {args.land_id}: {land}")
    print(f"Item tile {args.item_id}: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
