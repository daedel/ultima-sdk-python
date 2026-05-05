"""Files path discovery example.

Shows how to initialize Files and resolve known UO data filenames.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from ultima_sdk.files import Files

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    args = parser.parse_args()

    root = resolve_uo_root(args.uo_root)
    init_files(root, require=True)

    print("UO root:", Files.get_directory())

    names = [
        "client.exe",
        "art.mul",
        "artlegacymul.uop",
        "tiledata.mul",
        "hues.mul",
        "gumpart.mul",
        "gumpartlegacymul.uop",
        "sound.mul",
        "soundlegacymul.uop",
        "map0.mul",
        "map0legacymul.uop",
        "cliloc.enu",
    ]

    for name in names:
        path = Files.get_file_path(name)
        found = bool(path and Path(path).exists())
        print(f"{name:22} -> {path or 'not found'}{' (ok)' if found else ''}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
