# Copilot instructions (ultima-sdk-python)

## Big picture
- This is a Python port of the C# Ultima SDK: the public API favors C#-style “static classes” implemented as `@classmethod`s (e.g. `Files`, `Art`, `TileData`). See `ultima_sdk/__init__.py` and the module list in `README.md`.
- The core flow is: resolve the Ultima Online install directory → resolve data file paths → open `.idx`/`.mul` pairs via `FileIndex` → decode bytes into higher-level objects.

## Where to change code
- Edit source in `ultima_sdk/` (not `build/lib/…`, which is a generated copy).
- Tests live in `tests/` and are run with pytest.
- Examples are runnable modules under `examples/` (e.g. `python -m examples.simple_radar_example`).

## Key components & patterns
- Path discovery & configuration: `ultima_sdk/files.py` (`Files.initialize`, `Files.set_directory`, `Files.get_file_path`, `Files.require_file_path`).
  - `Files.initialize()` checks env vars `UO_ROOT` / `ULTIMA_ONLINE_DIR`, then Windows registry, then common paths.
  - Import-time side effect: `Files.initialize()` runs when `ultima_sdk.files` is imported; set `UO_ROOT` early to avoid warnings in tools/tests.
- Indexed file reading: `ultima_sdk/file_index.py` (`FileIndex`).
  - `FileIndex(idx_path, mul_path)` loads disk `.idx` (3 x int32 per entry); `read_raw(id)` seeks into the `.mul`.
  - Tests also use `FileIndex.load_from_bytes()` with 3 x uint32 entries for in-memory fixtures.
- Rendering: `ultima_sdk/rendering.py`.
  - `image_from_pixels(width, height, pixels)` supports RGBA, RGB, or UO 16-bit 5-5-5 (“UO16”).
- Art decoding: `ultima_sdk/art.py`.
  - `Art.get_art(id)` reads raw bytes and tries `_decode_static_art` (raw `uint16 width/height + pixels` first, then classic RLE).
  - `ArtData.to_image()` / `ArtTile.to_image()` delegates to `rendering.image_from_pixels()`.

## Tests & local workflows
- Install for development: `python -m pip install -e .` then `python -m pip install -r requirements.txt`.
- Run tests: `pytest -q` (see `scripts/dev_install.ps1` / `scripts/dev_install.sh`).
- Tests are designed to avoid needing real UO client files:
  - Prefer `tmp_path` + small synthetic `.idx/.mul` fixtures (see `tests/test_art_decode.py`).
  - Prefer patching `builtins.open` / `Path.exists` for I/O boundaries (see `tests/test_client.py`, `tests/test_art.py`).
  - Note: `ultima_sdk/__init__.py` injects `patch` and `mock_open` into `builtins` for some tests.

## Linting
- `requirements.txt` includes `flake8`; if you add lint fixes, prefer minimal, localized changes consistent with existing style.
