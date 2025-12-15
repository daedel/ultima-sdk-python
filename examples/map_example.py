"""Map / TileMatrix example.

Reads a few map tiles and prints their (tile_id, z).
"""

from __future__ import annotations

import argparse

from ultima_sdk.map import Map

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    parser.add_argument("--map", type=int, default=0, help="Map facet (default: 0)")
    parser.add_argument("--x", type=int, default=0)
    parser.add_argument("--y", type=int, default=0)
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    Map.initialize()

    m = Map.get_map(int(args.map))
    if m is None:
        print("Map not available")
        return 1

    tile = m.get_tile(int(args.x), int(args.y))
    print(f"Map{args.map} tile ({args.x},{args.y}) -> {tile}")
    # Also print a small 3x3 neighborhood.
    for dy in range(3):
        row = []
        for dx in range(3):
            t = m.get_tile(int(args.x) + dx, int(args.y) + dy)
            row.append(t)
        print(row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
