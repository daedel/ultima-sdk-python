# Examples for ultima_sdk

This directory contains runnable example scripts for the `ultima_sdk` package.

Run examples from the project root using:

```bash
python -m examples.<example_name>
```

## Client directory

Many examples require a real Ultima Online client directory.

Provide the path using either:

- `--uo-root /path/to/uo`, or
- environment variables: `UO_ROOT`, `ULTIMA_ONLINE_DIR`, or `ULTIMA_SDK_UO_ROOT`

Example:

```bash
python -m examples.files_example --uo-root /path/to/ultima_online
```

PowerShell:

```powershell
$env:UO_ROOT = 'F:\Program Files (x86)\Electronic Arts\Ultima Online Classic'
python -m examples.files_example
```

## Output

Many examples write generated files into an output directory using `--out`.
The default output directory is `out` when supported by the script.

If Pillow is unavailable, image examples fall back to writing `.ppm` files instead of `.png` or `.gif`.

## Example categories

### Synthetic examples (no client needed)

- `python -m examples.binary_extensions_example`
- `python -m examples.file_index_example`
- `python -m examples.render_tile_example`
- `python -m examples.rendering_example`
- `python -m examples.def_files_example`
- `python -m examples.uop_example`
- `python -m examples.exceptions_example`
- `python -m examples.verdata_ids_example`
- `python -m examples.tile_matrix_example`
- `python -m examples.animation_edit_example`
- `python -m examples.package_init_example`
- `python -m examples.all_in_one_example` (comprehensive demo with debug output)

### Client-backed examples (require a UO client directory)

- `python -m examples.files_example --uo-root /path/to/ultima_online`
- `python -m examples.tiledata_example --uo-root /path/to/ultima_online`
- `python -m examples.hues_example --uo-root /path/to/ultima_online --out out`
- `python -m examples.art_example --uo-root /path/to/ultima_online --out out`
- `python -m examples.gumps_example --uo-root /path/to/ultima_online --out out`
- `python -m examples.textures_example --uo-root /path/to/ultima_online --out out`
- `python -m examples.light_example --uo-root /path/to/ultima_online --out out`
- `python -m examples.radar_col_example --uo-root /path/to/ultima_online`
- `python -m examples.map_example --uo-root /path/to/ultima_online`
- `python -m examples.multis_example --uo-root /path/to/ultima_online`
- `python -m examples.sound_example --uo-root /path/to/ultima_online --out out`
- `python -m examples.string_list_example --uo-root /path/to/ultima_online`
- `python -m examples.skills_example --uo-root /path/to/ultima_online`
- `python -m examples.skill_groups_example --uo-root /path/to/ultima_online`
- `python -m examples.animations_example --uo-root /path/to/ultima_online --out out`
- `python -m examples.animations_gif_example --uo-root /path/to/ultima_online --out out`
- `python -m examples.equipconv_example --uo-root /path/to/ultima_online`
- `python -m examples.verdata_example --uo-root /path/to/ultima_online`

### Web applications

- `python examples/asset_viewer/app.py --uo-root /path/to/ultima_online` (comprehensive web-based asset viewer)
```
