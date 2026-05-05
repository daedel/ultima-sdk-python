"""StringList example.

Reads cliloc entries from the configured client files.
"""

from __future__ import annotations

import argparse

from ultima_sdk.string_list import StringList

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    parser.add_argument("--id", type=int, default=3000001, help="Cliloc id")
    args = parser.parse_args()

    init_files(
        resolve_uo_root(args.uo_root),
        require=True,
        require_any=("cliloc.enu", "cliloc.deu", "cliloc.custom1", "cliloc.custom2"),
    )

    StringList.initialize()
    for entry_id in range(args.id, args.id + 5):
        print(f"cliloc[{entry_id}] = {StringList.get_string(entry_id)!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
