"""TileMatrix example (synthetic, no client files required).

Demonstrates `TileMatrix.set_tile()` and `get_tile()` using the in-memory `tiles` list.

Run:
  python -m examples.tile_matrix_example
"""

from __future__ import annotations

from ultima_sdk.tile_matrix import TileMatrix


def main() -> int:
    m = TileMatrix(map_id=0, width=8, height=8, map_path=None)
    m.set_tile(0, 0, tile_id=0x00AA, altitude=5)
    m.set_tile(1, 0, tile_id=0x00AB, altitude=6)
    m.set_tile(0, 1, tile_id=0x00AC, altitude=-3)

    print("tile(0,0):", m.get_tile(0, 0))
    print("tile(1,0):", m.get_tile(1, 0))
    print("tile(0,1):", m.get_tile(0, 1))
    print("tile(7,7):", m.get_tile(7, 7))
    print("tile(8,8):", m.get_tile(8, 8))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
