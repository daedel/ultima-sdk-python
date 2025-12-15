"""StringList example.

Prints a few cliloc entries from the configured client.
"""

from __future__ import annotations

import argparse

from ultima_sdk.string_list import StringList

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    parser.add_argument("--id", type=int, default=3000001, help="Cliloc id (default: 3000001)")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True, require_any=("cliloc.enu", "cliloc.deu"))
    StringList.initialize()

    s = StringList.get_string(int(args.id))
    print(f"cliloc[{args.id}] = {s!r}")
    # Also show a small range around it.
    for i in range(int(args.id), int(args.id) + 5):
        print(f"  {i}: {StringList.get_string(i)!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
