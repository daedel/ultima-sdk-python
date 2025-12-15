"""Files path discovery example.

Run (with a real client):
  python -m examples.files_example --uo-root "C:\\Path\\To\\Ultima Online"

Or set env var UO_ROOT / ULTIMA_ONLINE_DIR.
"""

from __future__ import annotations

import argparse
import os

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
        "artLegacyMUL.uop",
        "tiledata.mul",
        "hues.mul",
        "gumpart.mul",
        "gumpartLegacyMUL.uop",
        "sound.mul",
        "soundLegacyMUL.uop",
        "map0.mul",
        "map0LegacyMUL.uop",
        "cliloc.enu",
    ]
    for name in names:
        try:
            p = Files.get_file_path(name)
        except Exception:
            p = None
        exists = bool(p and os.path.exists(p))
        print(f"{name:22} -> {p} {'(ok)' if exists else ''}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
