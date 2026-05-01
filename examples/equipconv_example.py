"""EquipConv example.

Loads equipconv.def from the client if available and converts an item id.
"""

from __future__ import annotations

import argparse

from ultima_sdk.equipconv import EquipConv

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    parser.add_argument(
        "--item",
        type=lambda s: int(s, 0),
        default=0x0EED,
        help="Item id (default: 0x0EED)",
    )
    parser.add_argument("--body", type=int, default=None, help="Optional body id")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    ok = EquipConv.initialize()
    print("EquipConv initialized:", ok)
    converted = EquipConv.convert(int(args.item), body_id=args.body)
    print(f"Item 0x{int(args.item):04X} -> 0x{converted:04X} (body={args.body})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
