"""RadarCol example.

Loads radar color values from radarcol.mul and prints them.
"""

from __future__ import annotations

import argparse

from ultima_sdk.radar_col import RadarCol

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)

    RadarCol.initialize()
    for index in range(16):
        color = RadarCol.get_color(index)
        print(f"Index {index:2d}: 0x{color:04X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
