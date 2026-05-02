<![CDATA[<p align="center">
  <img src="https://raw.githubusercontent.com/UltimaWorks/ultima-sdk-python/main/ultima-sdk-python%20banner.png" alt="Ultima SDK Python Banner" width="100%" />
</p>

![PyPI Python Version](https://img.shields.io/pypi/pyversions/ultima-sdk-python)
[![GitHub license](https://img.shields.io/github/license/UltimaWorks/ultima-sdk-python)](LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/UltimaWorks/ultima-sdk-python)](https://github.com/UltimaWorks/ultima-sdk-python/commits/main)

# Ultima SDK Python

A comprehensive 1:1 Python conversion of the C# Ultima Online SDK. This library provides full read access to Ultima Online client data files (`.mul`, `.idx`, and UOP formats) for use in tools, servers, and modding pipelines.

## Features

- Full access to UO client data files: Art, Animations, Gumps, TileData, Hues, Map, and more
- Support for both legacy `.mul/.idx` and modern `.uop` file formats
- Built-in PNG rendering helpers via Pillow
- Automatic client directory discovery on Windows (registry lookup)
- Manifest-based override support for custom client data
- Typed API with type hints throughout
- Comprehensive test suite including mocked and real-client smoke tests

## Installation

### From PyPI (coming soon)

```bash
pip install ultima-sdk-python
```

### From Source

```bash
git clone https://github.com/UltimaWorks/ultima-sdk-python.git
cd ultima-sdk-python
pip install -e .
```

### Requirements

- **Python 3.10+**
- **Pillow 10.0+**
- An Ultima Online client installation (for reading `.mul`, `.idx`, and `.uop` files)

## Quick Start

```python
from ultima_sdk import Files, TileData, Art, Animations, Hues

# Initialize file paths (auto-detects UO client on Windows)
Files.initialize()  # or: Files.initialize("C:\\Ultima Online")

# Load tile data
TileData.initialize()
land_tile = TileData.get_land_tile(0)  # Get grass tile
static_tile = TileData.get_static_tile(3388)  # Get a static item

# Load hues
Hues.initialize()
hue_0 = Hues.get_hue(0)  # Default hue

# Load art
Art.initialize()
art = Art.get_art(0x4001)  # Load art by graphic ID
if art:
    img = art.to_image()  # Convert to PIL Image
    img.save("output.png")

# Load animations
Animations.initialize()
anim = Animations.get_animation(body=1, action=0, direction=0)
```

## Module Reference

### Files

The `Files` class manages all UO client data file paths and discovery.

```python
from ultima_sdk import Files

# Auto-detect client directory (Windows registry)
Files.initialize()

# Or specify manually
Files.initialize("/path/to/ultima_online")

# Check if a file exists
if Files.file_exists("artidx.mul"):
    print("Art index found!")

# Get absolute path to a file
art_path = Files.get_file_path("artidx.mul")
```

### TileData

Reads `tiledata.mul` for land and static tile definitions.

```python
from ultima_sdk import TileData

TileData.initialize()

# Land tiles (ground textures)
land = TileData.get_land_tile(0)  # Grass
print(land.name, land.flags)

# Static tiles (items, walls, furniture)
static = TileData.get_static_tile(3388)  # Wooden chest
print(static.name, static.height)
```

### Hues

Reads `hues.mul` for color/shader data.

```python
from ultima_sdk import Hues

Hues.initialize()
hue = Hues.get_hue(1)  # Red hue
print(hue.name)  # "Crimson"
```

### Art

Reads `artidx.mul` / `art.mul` for static item graphics.

```python
from ultima_sdk import Art

Art.initialize()
art = Art.get_art(0x4001)  # Load by graphic ID
if art:
    img = art.to_image()  # Returns PIL.Image
    img.save("item.png")
```

### Animations

Reads `anim.idx` / `anim.mul` and variant files for character/object animations.

```python
from ultima_sdk import Animations

Animations.initialize()
# Get a single frame
frame = Animations.get_animation(body=1, action=0, direction=0)

# Export as GIF
Animations.export_gif(1, 5, "character.gif")
```

### Gumps

Reads `gumpidx.mul` / `gumpart.mul` for UI element graphics.

```python
from ultima_sdk import Gumps

Gumps.initialize()
gump = Gumps.get_gump(gump_id=0x829)
if gump:
    img = gump.to_image()
```

### Map

Reads map data including statics, map markers, and multi-object placements.

```python
from ultima_sdk import Map

Map.initialize()
# Get statics at a location
statics = Map.get_statics(0, 1396, 819)  # Britain
for s in statics:
    print(s.item_id, s.x, s.y, s.z)
```

### Skills

Reads `skills.def` for skill definitions.

```python
from ultima_sdk import Skills

Skills.initialize()
for skill_id in range(150):
    skill = Skills.get_skill(skill_id)
    if skill:
        print(f"{skill.name}: gainrate={skill.gain_rate}")
```

### Rendering

All art, animation, and gump objects have a `.to_image()` method that returns a `PIL.Image`.

```python
from ultima_sdk import Art

Art.initialize()
art = Art.get_art(0x4051)
img = art.to_image()
img.save("output.png")
```

## File Structure

```
ultima-sdk-python/
├── pyproject.toml
├── README.md
├── LICENSE
├── .github/workflows/      # CI/CD pipelines
├── examples/               # Usage examples for each module
├── scripts/                # Utility scripts
├── tests/                  # Test suite
└── ultima_sdk/
    ├── __init__.py         # Package entry point
    ├── files.py            # File path management
    ├── tiledata.py         # TileData.mul reader
    ├── hues.py             # Hues.mul reader
    ├── art.py              # Art graphics reader
    ├── animations.py       # Animation reader
    ├── gumps.py            # Gump graphics reader
    ├── map.py              # Map data reader
    ├── skills.py           # Skills.def reader
    ├── multis.py           # Multi-object data
    ├── textures.py         # Texture reader
    ├── sound.py            # Sound/music reader
    ├── uop.py              # UOP file format support
    ├── verdata.py          # Version data (patching)
    ├── rendering.py        # PIL image helpers
    └── ...                 # Other utility modules
```

## Examples

The [`examples/`](examples/) directory contains runnable scripts for every major module:

| File | Description |
|------|-------------|
| `art_example.py` | Load and save art tiles as PNG |
| `animations_gif_example.py` | Export animations to GIF |
| `map_example.py` | Query static objects on a map |
| `rendering_example.py` | Render art/animations to images |
| `uop_example.py` | Work with UOP-format data files |
| `verdata_example.py` | Apply patch data from verdata |
| ... | See [examples/](examples/) for all 30+ examples |

## Tests

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=ultima_sdk --cov-report=term

# Run a specific test module
pytest tests/test_art.py -v
```

## Platform Support

| Platform | Support | Notes |
|----------|---------|-------|
| Windows | Full | Auto-detection via registry |
| Linux | Supported | Manual path configuration |
| macOS | Supported | Manual path configuration |

## License

Written under the Pickleware License. See [LICENSE](LICENSE) for full terms.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, code standards, and the PR workflow.

## Related Projects

- [UOFiddler](https://github.com/jedi661/UoFiddlerPixel) — Original C# Ultima SDK this project converts from
- [ServUO](https://github.com/ServUO/ServUO) — Popular Ultima Online server implementation
- [JSmith.UoSdk](https://github.com/j我的小装备/JSmith.UoSdk) — .NET SDK for UO client data

## Support

For issues, questions, or feature requests, please open an issue on the [GitHub Issues](https://github.com/UltimaWorks/ultima-sdk-python/issues) page.
]]>