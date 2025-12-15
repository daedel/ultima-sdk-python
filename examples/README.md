# Examples for ultima_sdk

Run the example scripts from the `SDK` directory (project root). Example:

```bash
python -m examples.simple_radar_example
```

Many examples require a real Ultima Online client directory.

If Pillow isn't installed, image examples will write `.ppm` files instead of `.png`/`.gif`.

Provide it via `--uo-root` or set env var `UO_ROOT` / `ULTIMA_ONLINE_DIR`.

PowerShell:

```powershell
$env:UO_ROOT="F:\\Program Files (x86)\\Electronic Arts\\Ultima Online Classic"
python -m examples.files_example
```

The script demonstrates basic usage of `ultima_sdk.radar_col.RadarCol`.

## Rendering example

Writes a small PNG (`out.png`) using the built-in Pillow rendering helpers:

```bash
python -m examples.render_tile_example

## Suite

Synthetic (no client needed):

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

Client-backed (needs `--uo-root` or `UO_ROOT`):

- `python -m examples.files_example`
- `python -m examples.tiledata_example`
- `python -m examples.hues_example`
- `python -m examples.art_example`
- `python -m examples.gumps_example`
- `python -m examples.textures_example`
- `python -m examples.light_example`
- `python -m examples.radar_col_example`
- `python -m examples.map_example`
- `python -m examples.multis_example`
- `python -m examples.sound_example`
- `python -m examples.string_list_example`
- `python -m examples.skills_example`
- `python -m examples.skill_groups_example`
- `python -m examples.animations_gif_example`
- `python -m examples.animations_example`
- `python -m examples.equipconv_example`
- `python -m examples.verdata_example`

Windows client interaction:

- `python -m examples.client_example`
```
