"""Map example.

Loads a map facet and prints terrain data for a coordinate neighborhood.
"""

from __future__ import annotations

import argparse

from ultima_sdk.map import Map

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    parser.add_argument("--map", type=int, default=0, help="Map facet id")
    parser.add_argument("--x", type=int, default=0, help="Tile x coordinate")
    parser.add_argument("--y", type=int, default=0, help="Tile y coordinate")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)

    Map.initialize()
    map_data = Map.get_map(args.map)
    if map_data is None or map_data.tile_matrix is None:
        print(f"Map {args.map} is not available")
        return 1

    center = map_data.get_tile(args.x, args.y)
    print(f"Map {args.map} tile ({args.x},{args.y}) -> {center}")

    for dy in range(3):
        row = []
        for dx in range(3):
            row.append(map_data.get_tile(args.x + dx, args.y + dy))
        print(row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
