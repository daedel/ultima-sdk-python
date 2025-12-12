# Ultima-SDK-Python

[Project on GitHub](https://github.com/UltimaWorks/ultima-sdk-python/)

## Index

- [Ultima-SDK-Python](#ultima-sdk-python)
  - [Index](#index)
  - [Wiki](#wiki)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Module Reference](#module-reference)
    - [Files](#files)
    - [TileData](#tiledata)
    - [Hues](#hues)
    - [Client](#client)
    - [Art, Animations, Gumps, Sound](#art-animations-gumps-sound)
    - [Map](#map)
    - [Skills](#skills)
  - [File Structure](#file-structure)
  - [API Design](#api-design)
  - [Platform Support](#platform-support)
  - [License](#license)
  - [Contributing](#contributing)
  - [Original C# SDK](#original-c-sdk)
  - [Support](#support)

A comprehensive 1:1 conversion of the C# Ultima Online SDK into pure Python.

This SDK provides full access to Ultima Online client data files, including:

- Art and graphics (static items, gumps, light sources)
- Animations and character data
- Tile data and map information
- Sound and music files
- Hue/color palette management
- Client window interaction
- Multi-tile object data (houses, ships)
- String and skill information

## Wiki

For detailed documentation, examples, and development guides, see the project [Wiki](https://github.com/UltimaWorks/ultima-sdk-python/wiki)

Contents you'll find there:

- Overview — project goals and compatibility notes
- Getting Started — installation, configuration, and quick-start examples
- Modules & API Reference — detailed docs for Files, Art, TileData, Hues, Map, Client, etc.
- Tutorials — loading assets, reading maps, working with animations, and common use cases
- Migration Guide — tips for translating C# SDK patterns to Python idioms
- Contributing & Development — coding standards, tests, and how to run the test suite
- Troubleshooting & FAQ — common issues and resolutions
- Changelog & Releases — notable changes and upgrade notes

If a topic is missing or outdated, please open an issue or submit a PR to improve the Wiki.

---

## Installation

```bash
pip install -e .
```

Or install directly:

```bash
python setup.py install
```

---

## Quick Start

```python
from ultima_sdk import Files, Art, TileData, Hues, Animations

# Initialize with your UO client directory
Files.initialize("/path/to/Ultima Online")

# Load tile data
TileData.initialize()
land_tile = TileData.get_land_tile(0)

# Load hues
Hues.initialize()
hue = Hues.get_hue(0)

# Load art
Art.initialize()
art = Art.get_art(0x4001)  # Example static item

# Load animations
Animations.initialize()
anim = Animations.get_animation(body=1, action=0, direction=0)
```

---

## Module Reference

### Files

Manages Ultima Online data file paths and discovery.

```python
import os
from ultima_sdk import Files

def ensure_uo_directory():
  # Try auto-discover; don't fail hard if it raises
  try:
    Files.initialize()
  except Exception:
    pass

  # Check if a known file can be resolved
  def has_known_file():
    try:
      art_path = Files.get_file_path("art.mul")
    except Exception:
      return False
    return bool(art_path and os.path.exists(art_path))

  if not has_known_file():
    # Prompt user until a valid UO directory is provided
    while True:
      try:
        user_dir = input("Ultima Online directory not found. Please enter the path to your UO client: ").strip()
      except (KeyboardInterrupt, EOFError):
        raise SystemExit("UO directory is required to continue.")

      if not user_dir:
        continue
      if not os.path.isdir(user_dir):
        print("Path does not exist or is not a directory. Try again.")
        continue

      # Basic validation for common UO files
      valid = any(os.path.exists(os.path.join(user_dir, fn)) for fn in ("art.mul", "client.exe", "ultima.exe"))
      if not valid:
        print("Directory doesn't contain expected UO files (e.g. art.mul). Try again.")
        continue

      # Set directory in SDK and export to environment
      Files.set_directory(user_dir)
      os.environ["UO_DIR"] = user_dir

      # Re-run initialize in case SDK needs it
      try:
        Files.initialize()
      except Exception:
        pass

      if has_known_file():
        break
      else:
        print("Could not verify files after setting directory. Try again.")

ensure_uo_directory()

# Get file paths
art_path = Files.get_file_path("art.mul")
print("art.mul path:", art_path)
```

### TileData

Access tile properties and static/dynamic item information.

```python
from ultima_sdk import TileData

TileData.initialize()

# Get land tile
land = TileData.get_land_tile(0)
print(f"Land: {land['name']}, Flags: {hex(land['flags'])}")

# Get item tile
item = TileData.get_item_tile(0x4001)
print(f"Item: {item['name']}, Weight: {item['weight']}")
```

### Hues

Access color palette and hue information.

```python
from ultima_sdk import Hues

Hues.initialize()

# Get specific hue
hue = Hues.get_hue(0)

# Get color from hue
color = hue.get_color(0)
```

### Client

Interact with running Ultima Online client.

```python
from ultima_sdk import Client

# Check if client is running
if Client.is_running():
    # Bring window to foreground
    Client.bring_to_top()

    # Send text to client
    Client.send_text("hello world")
```

### Art, Animations, Gumps, Sound

Load graphics and media assets.

```python
from ultima_sdk import Art, Animations, Gumps, Sound

Art.initialize()
art_data = Art.get_art(graphic_id)

Animations.initialize()
anim = Animations.get_animation(body, action, direction)

Gumps.initialize()
gump = Gumps.get_gump(gump_id)

Sound.initialize()
sound = Sound.get_sound(sound_id)
```

### Map

Access map and terrain data.

```python
from ultima_sdk import Map

Map.initialize()

map_data = Map.get_map(map_id=0)  # Felucca
tile = map_data.get_tile(1000, 1000)
```

### Skills

Access skill information.

```python
from ultima_sdk import Skills

Skills.initialize()

skill = Skills.get_skill(0)  # Alchemy
combat_skill = Skills.find_skill("Magery")
```

---

## File Structure

```text
ultima-sdk-python/
├── setup.py
├── README.md
├── LICENSE
├── MANIFEST.in
└── ultima_sdk/
    ├── __init__.py
    ├── exceptions.py
    ├── binary_extensions.py
    ├── files.py
    ├── client.py
    ├── tiledata.py
    ├── hues.py
    ├── art.py
    ├── animations.py
    ├── gumps.py
    ├── sound.py
    ├── light.py
    ├── textures.py
    ├── multis.py
    ├── map.py
    ├── skills.py
    ├── animation_edit.py
    ├── string_list.py
    ├── radar_col.py
    ├── skill_groups.py
    ├── file_index.py
    └── tile_matrix.py
```

---

## API Design

This SDK maintains API compatibility with the C# Ultima SDK while following Python idioms:

- Static utility classes use `@classmethod` decorators
- Exceptions inherit from `UltimaSdkException`
- Binary I/O uses `BinaryReader`/`BinaryWriter` helpers
- File discovery uses platform-specific registry queries (Windows) and common paths
- Lazy initialization pattern for resource-heavy modules

---

## Platform Support

- **Windows**: Full support including registry-based client discovery
- **Linux/macOS**: Supported with manual directory configuration

---

## License

Pickled License - See LICENSE file for details

---

## Contributing

Contributions welcome! Please follow PEP 8 style guidelines and add tests for new features.

---

## Original C# SDK

This is a conversion of the Ultima SDK originally developed for the UoFiddler project: [UOFiddler](https://github.com/jedi661/UoFiddlerPixel)

---

## Support

For issues, questions, or suggestions, please open an issue on [GitHub Issues](https://github.com/UltimaWorks/ultima-sdk-python/issues).
