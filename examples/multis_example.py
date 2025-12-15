"""Multis example.

Loads a multi and prints the first few components.
"""

from __future__ import annotations

import argparse

from ultima_sdk.multis import Multis

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    parser.add_argument("--id", type=int, default=0, help="Multi id (default: 0)")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True, require_any=("multi.mul", "multi.idx"))
    Multis.initialize()

    m = Multis.get_multi(int(args.id))
    if m is None:
        print("Multi not found")
        return 1

    print(f"Multi {m.multi_id} components: {len(m.components)}")
    for c in m.components[:10]:
        print(f"  item=0x{c.item_id:04X} x={c.x} y={c.y} z={c.z} flags={c.flags} unk1={c.unk1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
