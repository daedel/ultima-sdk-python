"""Verdata example.

Loads verdata.mul and reports patch counts for supported file ids.
"""

from __future__ import annotations

import argparse

from ultima_sdk.verdata import Verdata, FILE_IDS

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    args = parser.parse_args()

    init_files(
        resolve_uo_root(args.uo_root),
        require=True,
        require_any=("verdata.mul",),
    )

    initialized = Verdata.initialize()
    print(f"Verdata initialized: {initialized}")

    if not initialized:
        return 1

    stats = Verdata.apply()
    print("Applied patches:")
    for key, count in sorted(stats.items()):
        print(f"  {key}: {count}")

    for file_id in [FILE_IDS.ART_MUL, FILE_IDS.GUMPART_MUL, FILE_IDS.MAP0_MUL]:
        print(
            f"Has patch file_id={file_id}: {Verdata.has_patch(file_id, 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
