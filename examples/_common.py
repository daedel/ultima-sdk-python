"""Shared helpers for examples.

These examples are designed to either:
- run purely on synthetic data (no client install required), or
- use a real UO client directory when provided via --uo-root or env vars.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

from ultima_sdk.files import Files

UO_ROOT_ENV_VARS: tuple[str, ...] = (
    "ULTIMA_ONLINE_DIR",
    "UO_ROOT",
    "ULTIMA_SDK_UO_ROOT",
)


def add_uo_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--uo-root",
        default=None,
        help="Path to an installed Ultima Online client directory (or set UO_ROOT).",
    )


def add_out_arg(parser: argparse.ArgumentParser, default: str = "out") -> None:
    parser.add_argument(
        "--out",
        default=default,
        help="Output directory for generated files (default: out).",
    )


def resolve_uo_root(cli_value: str | None) -> str | None:
    if cli_value:
        return cli_value
    for key in UO_ROOT_ENV_VARS:
        value = os.getenv(key)
        if value:
            return value
    return None


def init_files(
    uo_root: str | None, *, require: bool = True, require_any: Iterable[str] = ()
) -> str | None:
    """Initialize Files and optionally require a usable client directory."""
    if uo_root:
        Files.set_directory(uo_root)

    # Files.initialize() may warn if it cannot discover a client; that's fine for examples.
    try:
        Files.initialize()
    except Exception:
        pass

    if not require:
        return uo_root

    # Validate by resolving at least one known file.
    candidates = list(require_any) or [
        "art.mul",
        "artLegacyMUL.uop",
        "gumpart.mul",
        "gumpartLegacyMUL.uop",
        "tiledata.mul",
    ]
    for name in candidates:
        try:
            path = Files.get_file_path(name)
        except Exception:
            path = None
        if path and os.path.exists(path):
            return uo_root

    hint = (
        "This example needs a UO client directory.\n\n"
        "Set env var UO_ROOT (or ULTIMA_ONLINE_DIR), or pass --uo-root.\n"
        "Example (PowerShell):\n"
        '  $env:UO_ROOT="F:\\Program Files (x86)\\Electronic Arts\\Ultima Online Classic"\n'
        "  python -m examples.files_example\n"
    )
    raise SystemExit(hint)


def ensure_out_dir(out_dir: str | Path) -> Path:
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _uo16_to_rgb_bytes(pixels_uo16: bytes) -> bytes:
    # Convert UO 16-bit 5-5-5 pixels to 24-bit RGB.
    # Layout: rrrrrgggggbbbbb (bits 10..14, 5..9, 0..4)
    if pixels_uo16 is None:
        return b""
    if (len(pixels_uo16) & 1) != 0:
        pixels_uo16 = pixels_uo16[:-1]

    out = bytearray((len(pixels_uo16) // 2) * 3)
    oi = 0
    for i in range(0, len(pixels_uo16), 2):
        v = pixels_uo16[i] | (pixels_uo16[i + 1] << 8)
        r5 = (v >> 10) & 0x1F
        g5 = (v >> 5) & 0x1F
        b5 = v & 0x1F
        # Expand 5->8 bits by bit replication.
        out[oi] = (r5 << 3) | (r5 >> 2)
        out[oi + 1] = (g5 << 3) | (g5 >> 2)
        out[oi + 2] = (b5 << 3) | (b5 >> 2)
        oi += 3
    return bytes(out)


def write_ppm_rgb(path: str | Path, width: int, height: int, rgb_bytes: bytes) -> Path:
    p = Path(path)
    header = f"P6\n{int(width)} {int(height)}\n255\n".encode("ascii")
    p.write_bytes(header + (rgb_bytes or b""))
    return p


def save_uo16_image(
    width: int, height: int, pixels_uo16: bytes, out_path: str | Path
) -> Path:
    """Save a UO16 buffer as PNG (if Pillow available) else as PPM.

    Args:
        out_path: Desired output path. If PNG save fails due to missing Pillow,
                  the function writes a `.ppm` file next to it.
    """
    out_path = Path(out_path)
    try:
        from ultima_sdk.rendering import image_from_pixels

        img = image_from_pixels(
            int(width), int(height), pixels_uo16, format_hint="UO16"
        )
        img.save(str(out_path), format="PNG")
        return out_path
    except ImportError:
        ppm = out_path.with_suffix(".ppm")
        rgb = _uo16_to_rgb_bytes(pixels_uo16)
        return write_ppm_rgb(ppm, int(width), int(height), rgb)
