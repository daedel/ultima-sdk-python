# 🚀 QUICK START - Ultima SDK Python

## ⚡ 60-Second Setup

```bash
# 1. Download & Extract
unzip ultima-sdk-python.zip

# 2. Install
cd ultima-sdk-python
pip install -e .

# 3. Verify
python -c "from ultima_sdk import Files; print('✓ Ready!')"
```

## 📝 First Script

Create `test_ultima.py`:

```python
from ultima_sdk import Files, TileData, Hues

# Initialize
Files.set_directory("/path/to/Ultima Online")
TileData.initialize()
Hues.initialize()

# Use it
tile = TileData.get_land_tile(0)
hue = Hues.get_hue(0)

print(f"Tile: {tile['name']}")
print(f"Hue Color: {hex(hue.get_color(0))}")
```

Run it:

```bash
python test_ultima.py
```

## 🎯 What Each File Does

### ultima-sdk-python.zip (Main Package)

- Complete Python SDK
- 27 modules ready to use
- No external dependencies
- MIT licensed

### README.md (Inside ZIP)

- Getting started guide
- Installation help
- API overview
- Example code

### INTEGRATION_GUIDE.md (Separate)

- Architecture details
- Extension examples
- C# to Python conversion guide
- Testing patterns

### MANIFEST.md (Quick Reference)

- File listing
- Installation options
- Platform support table
- Version information

## 📱 Installation Methods

### Method 1: Development (Recommended)

```bash
unzip ultima-sdk-python.zip
cd ultima-sdk-python
pip install -e .
```

### Method 2: Regular Install

```bash
unzip ultima-sdk-python.zip
cd ultima-sdk-python
pip install .
```

### Method 3: Direct

```bash
python setup.py install
```

## ✅ Verify Installation

```python
# Test import
python -c "from ultima_sdk import Files; print('✓')"

# Test all modules
python -c "from ultima_sdk import *; print('✓ All modules loaded')"
```

## 🎮 Next Steps

### 1. Configure Path

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

### 2. Load Data

```python
from ultima_sdk import TileData, Hues, Art

TileData.initialize()
Hues.initialize()
Art.initialize()
```

### 3. Access Data

```python
# Get a tile
tile = TileData.get_land_tile(0)
print(tile['name'], tile['flags'])

# Get a hue
hue = Hues.get_hue(0)
print(hue.get_color(0))

# Get art
# art = Art.get_art(0x4001)
```

## 🔧 Common Tasks

### Task 1: Find Tile by Name

```python
from ultima_sdk import TileData

TileData.initialize()

for i in range(1000):
    tile = TileData.get_land_tile(i)
    if tile and 'grass' in tile['name'].lower():
        print(f"{i}: {tile['name']}")
```

### Task 2: List All Hues

```python
from ultima_sdk import Hues

Hues.initialize()

for i in range(100):
    hue = Hues.get_hue(i)
    if hue:
        color = hue.get_color(0)
        print(f"Hue {i}: {hex(color)}")
```

### Task 3: Browse Available Files

```python
from ultima_sdk import Files

path = Files.get_file_path("art.mul")
print(f"Art file: {path}")

path = Files.get_file_path("tiledata.mul")
print(f"TileData file: {path}")
```

## 🐛 Troubleshooting

### "File not found" Error

```python
# Set the correct path
from ultima_sdk import Files

# Windows (auto-detected)
Files.initialize()

# Or manual
Files.set_directory("C:\\Games\\Ultima Online")

# Verify
path = Files.get_file_path("art.mul")
print(f"Found: {path}")  # Should not be None
```

### Import Error

```bash
# Verify installation
pip list | grep ultima

# Reinstall if needed
pip install -e .
```

### Permission Error (Linux)

```bash
# Run without sudo
pip install --user -e .
```

## 📚 Full Documentation

After extracting, read:

1. `README.md` - Complete overview
2. `INTEGRATION_GUIDE.md` - Advanced patterns
3. Module docstrings - In-code documentation

## 🎁 What You Have

✅ 27 production-ready modules
✅ Full API documentation
✅ Type hints throughout
✅ Zero dependencies
✅ MIT license
✅ Cross-platform support

## 🏁 You're Ready

That's it. You now have a complete, modern Python interface to Ultima Online data.

### Next: Build Something Awesome! 🚀

---

**Questions?** See the included documentation.
**Issues?** Check INTEGRATION_GUIDE.md for patterns and examples.
**Ready?** Start coding with `from ultima_sdk import Files`!

---

For more details:

- 📖 README.md - Full user guide
- 🔧 INTEGRATION_GUIDE.md - Developer guide  
- 📋 MANIFEST.md - File reference
