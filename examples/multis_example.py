"""Multis example.

Loads a multi-tile object definition and prints its first components.
"""

from __future__ import annotations

import argparse

from ultima_sdk.multis import Multis

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    parser.add_argument("--id", type=int, default=0, help="Multi id")
    args = parser.parse_args()

    init_files(
        resolve_uo_root(args.uo_root),
        require=True,
        require_any=("multi.mul", "multi.idx"),
    )

    Multis.initialize()
    multi = Multis.get_multi(args.id)
    if multi is None:
        print(f"Multi {args.id} not found")
        return 1

    print(f"Multi {multi.multi_id} components: {len(multi.components)}")
    for component in multi.components[:10]:
        print(
            f"  item=0x{component.item_id:04X} x={component.x} y={component.y} z={component.z} flags={component.flags} unk1={component.unk1}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
