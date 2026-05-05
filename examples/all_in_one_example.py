"""All-in-one example demonstrating the full Ultima SDK functionality.

This script runs through all major features of the ultima_sdk package,
with detailed CLI debug outputs showing what's happening at each step.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from ultima_sdk import (
    Art,
    FileIndex,
    Files,
    Hues,
    Light,
    Multis,
    RadarCol,
    TileData,
    UopFile,
    Verdata,
)
import ultima_sdk.binary_extensions as binary_extensions
import ultima_sdk.def_files as def_files
import ultima_sdk.equipconv as equipconv
import ultima_sdk.exceptions as exceptions
import ultima_sdk.file_index as file_index
import ultima_sdk.rendering as rendering
import ultima_sdk.skill_groups as skill_groups
import ultima_sdk.skills as skills
import ultima_sdk.sound as sound
import ultima_sdk.string_list as string_list
import ultima_sdk.textures as textures

from ._common import (
    add_out_arg,
    add_uo_root_arg,
    ensure_out_dir,
    init_files,
    resolve_uo_root,
)


def debug_print(msg: str, *args: Any) -> None:
    """Print debug message with formatting."""
    print(f"[DEBUG] {msg}", *args)


def section_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title.upper()}")
    print(f"{'='*60}")


def run_binary_extensions_example() -> None:
    """Demonstrate BinaryReader/BinaryWriter."""
    section_header("Binary Extensions Example")
    debug_print("Creating BinaryWriter...")
    writer = binary_extensions.BinaryWriter()
    writer.write_uint16(0xBEEF)
    writer.write_int32(-123)
    writer.write_string("hello world", null_terminated=True)

    data = writer.get_buffer() or b""
    debug_print(f"Written data: {data!r} (length: {len(data)})")

    debug_print("Creating BinaryReader from data...")
    reader = binary_extensions.BinaryReader(data)

    value_uint16 = reader.read_uint16()
    value_int32 = reader.read_int32()
    value_str = reader.read_string(null_terminated=True)

    debug_print(f"Read uint16: 0x{value_uint16:04X}")
    debug_print(f"Read int32: {value_int32}")
    debug_print(f"Read string: {value_str!r}")


def run_file_index_example() -> None:
    """Demonstrate FileIndex with synthetic data."""
    section_header("File Index Example")
    debug_print("Creating synthetic .idx data...")

    # Create synthetic idx data (3 uint32 per entry: offset, size, unknown)
    idx_data = b""
    for i in range(3):
        offset = i * 100
        size = 50
        unknown = 0
        idx_data += offset.to_bytes(4, 'little')
        idx_data += size.to_bytes(4, 'little')
        idx_data += unknown.to_bytes(4, 'little')

    debug_print(f"Created idx data: {len(idx_data)} bytes")

    debug_print("Loading FileIndex from synthetic data...")
    idx = FileIndex()
    idx.load_from_bytes(idx_data)

    debug_print(f"Loaded {len(idx.entries)} entries:")
    for i, entry in enumerate(idx.entries):
        debug_print(f"  Entry {i}: offset={entry.offset}, length={entry.length}, extra={entry.extra}")

    debug_print("Note: read_raw() requires actual .mul files on disk")


def run_rendering_example() -> None:
    """Demonstrate rendering functionality."""
    section_header("Rendering Example")
    debug_print("Creating sample pixel data...")

    width, height = 16, 16
    # Create a simple gradient pattern
    pixels = []
    for y in range(height):
        for x in range(width):
            r = int(255 * x / width)
            g = int(255 * y / height)
            b = 128
            pixels.extend([r, g, b])

    debug_print(f"Created {len(pixels)//3} pixels for {width}x{height} image")

    debug_print("Converting to image...")
    try:
        image = rendering.image_from_pixels(width, height, bytes(pixels))
        debug_print(f"Created image: {image.size} (PIL Image)")
    except Exception as e:
        debug_print(f"Image creation failed: {e}")


def run_def_files_example() -> None:
    """Demonstrate DEF files parsing."""
    section_header("DEF Files Example")
    debug_print("Creating synthetic DEF file content...")

    def_content = """# Sample DEF file
BodyConv 0x123 0x456
BodyConv 0x789 0xABC
# Comment line
SomeKey 100 200
"""

    debug_print("Parsing DEF content...")
    try:
        defs = {}
        for line in def_content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 3:
                key = parts[0]
                value1 = parts[1]
                value2 = parts[2]
                if key not in defs:
                    defs[key] = []
                defs[key].append((value1, value2))

        debug_print(f"Parsed definitions:")
        for key, values in defs.items():
            debug_print(f"  {key}: {values}")
    except Exception as e:
        debug_print(f"DEF parsing failed: {e}")


def run_uop_example() -> None:
    """Demonstrate UOP file handling."""
    section_header("UOP Example")
    debug_print("Creating synthetic UOP data...")

    # This is simplified; real UOP is complex
    debug_print("UOP files are complex; demonstrating hash creation...")
    try:
        from ultima_sdk.uop import create_hash
        hash_val = create_hash("sample_file.dat")
        debug_print(f"Created hash for 'sample_file.dat': 0x{hash_val:016X}")
    except Exception as e:
        debug_print(f"UOP hash creation failed: {e}")


def run_exceptions_example() -> None:
    """Demonstrate exception handling."""
    section_header("Exceptions Example")
    debug_print("Testing exception classes...")

    try:
        raise exceptions.FileAccessException("Test file access error")
    except exceptions.FileAccessException as e:
        debug_print(f"Caught FileAccessException: {e}")

    try:
        raise exceptions.FileParseError("Test parse error")
    except exceptions.FileParseError as e:
        debug_print(f"Caught FileParseError: {e}")


def run_client_features(out_dir: Path, has_client: bool) -> None:
    """Run client-dependent features."""
    section_header("Client-Dependent Features")

    if not has_client:
        debug_print("No UO client directory available - skipping client features")
        return

    debug_print("UO client directory available - running client features...")

    # Art
    debug_print("Initializing Art...")
    try:
        Art.initialize()
        debug_print("Art initialized successfully")
        # Try to get a known art piece
        art_id = 0x4000
        art_tile = Art.get_art(art_id)
        if art_tile:
            debug_print(f"Art {art_id:04X} exists")
            out_path = out_dir / f"art_{art_id:05X}.png"
            if Art.save_png(art_id, out_path):
                debug_print(f"Saved art to {out_path}")
            else:
                debug_print(f"Failed to save art {art_id:04X}")
        else:
            debug_print(f"Art {art_id:04X} not found")
    except Exception as e:
        debug_print(f"Art initialization failed: {e}")

    # TileData
    debug_print("Initializing TileData...")
    try:
        TileData.initialize()
        debug_print("TileData initialized successfully")
        # Get some tile info
        tile = TileData.get_land_tile(0)
        debug_print(f"Land tile 0: {tile}")
    except Exception as e:
        debug_print(f"TileData initialization failed: {e}")

    # Hues
    debug_print("Initializing Hues...")
    try:
        Hues.initialize()
        debug_print("Hues initialized successfully")
        hue = Hues.get_hue(1)
        debug_print(f"Hue 1: {hue}")
    except Exception as e:
        debug_print(f"Hues initialization failed: {e}")

    # Other features...
    features = [
        ("RadarCol", RadarCol, "radar colors"),
        ("Light", Light, "lighting data"),
        ("Multis", Multis, "multi-tile structures"),
        ("Verdata", Verdata, "version data"),
    ]

    for name, cls, desc in features:
        debug_print(f"Initializing {name} ({desc})...")
        try:
            cls.initialize()
            debug_print(f"{name} initialized successfully")
        except Exception as e:
            debug_print(f"{name} initialization failed: {e}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_uo_root_arg(parser)
    add_out_arg(parser)
    args = parser.parse_args()

    debug_print("Starting All-in-One Ultima SDK Example")
    debug_print(f"Python version: {sys.version}")
    debug_print(f"Working directory: {Path.cwd()}")

    # Try to initialize files (optional for synthetic examples)
    uo_root = resolve_uo_root(args.uo_root)
    has_client = False
    try:
        init_files(uo_root, require=False)
        has_client = True
        debug_print(f"UO client directory: {uo_root}")
    except SystemExit:
        debug_print("No UO client directory available - will skip client-dependent features")

    out_dir = ensure_out_dir(args.out)
    debug_print(f"Output directory: {out_dir}")

    # Run synthetic examples first
    run_binary_extensions_example()
    run_file_index_example()
    run_rendering_example()
    run_def_files_example()
    run_uop_example()
    run_exceptions_example()

    # Run client-dependent features
    run_client_features(out_dir, has_client)

    debug_print("\nAll-in-one example completed!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())