"""TileData example.

Prints a couple tile entries.
"""

from __future__ import annotations

import argparse

from ultima_sdk.tiledata import TileData

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True, require_any=("tiledata.mul",))
    TileData.initialize()

    land0 = TileData.get_land_tile(0)
    item0 = TileData.get_item_tile(0)
    print("Land[0] :", land0)
    print("Item[0] :", item0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
