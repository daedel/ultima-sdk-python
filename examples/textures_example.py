"""Textures example.

Tries to decode a landscape texture and write it as PNG.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.textures import Textures

from ._common import add_out_arg, add_uo_root_arg, ensure_out_dir, init_files, resolve_uo_root, save_uo16_image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    add_out_arg(parser)
    parser.add_argument("--id", type=int, default=0, help="Texture id (default: 0)")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True, require_any=("texmaps.mul", "texidx.mul"))
    out_dir = ensure_out_dir(args.out)

    Textures.initialize()

    candidates = [int(args.id)] + list(range(0, 128))
    for tex_id in candidates:
        try:
            t = Textures.get_texture(tex_id)
            if t is None:
                continue
            out_path = Path(out_dir) / f"texture_{tex_id:04d}.png"
            saved = save_uo16_image(t.width, t.height, t.pixels, out_path)
            print(f"Decoded texture {tex_id} -> {saved} ({t.width}x{t.height})")
            return 0
        except Exception:
            continue

    print("Could not decode any texture in 0..127.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
