"""Verdata example.

Attempts to load verdata.mul and print whether a known file id has patches.
"""

from __future__ import annotations

import argparse

from ultima_sdk.verdata import Verdata
from ultima_sdk.verdata_ids import IDS

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    args = parser.parse_args()

    init_files(
        resolve_uo_root(args.uo_root), require=True, require_any=("verdata.mul",)
    )
    Verdata.initialize()

    # Query a couple known ids; many installs will have none.
    for file_id in [IDS.ART_MUL, IDS.GUMPART_MUL, IDS.MAP0_MUL]:
        try:
            patch = Verdata.read_patch(file_id, 0)
        except Exception:
            patch = None
        print(f"Verdata patch file_id={file_id} entry=0 present={patch is not None}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
