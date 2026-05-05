"""TileMatrix example (synthetic, no client files required).

Demonstrates in-memory tile updates and reads.
"""

from __future__ import annotations

from ultima_sdk.tile_matrix import TileMatrix


def main() -> int:
    matrix = TileMatrix(map_id=0, width=8, height=8, map_path=None)
    matrix.set_tile(0, 0, tile_id=0x00AA, altitude=5)
    matrix.set_tile(1, 0, tile_id=0x00AB, altitude=6)
    matrix.set_tile(0, 1, tile_id=0x00AC, altitude=-3)

    print("tile(0,0):", matrix.get_tile(0, 0))
    print("tile(1,0):", matrix.get_tile(1, 0))
    print("tile(0,1):", matrix.get_tile(0, 1))
    print("tile(7,7):", matrix.get_tile(7, 7))
    print("tile(8,8):", matrix.get_tile(8, 8))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
