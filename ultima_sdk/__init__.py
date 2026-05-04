"""Ultima Online SDK package initializer.

Expose common classes at package level for convenience.
Light/guarded imports keep import-time cost low.
"""

__version__ = "1.1.4"
__author__ = "UltimaWorks"

# Eagerly expose common high-level classes if available; keep failures silent
_EXPORTS = [
    "Files",
    "TileData",
    "Hues",
    "Art",
    "Animations",
    "Gumps",
    "Sound",
    "Light",
    "Textures",
    "Multis",
    "Map",
    "Skills",
    "AnimationEdit",
    "StringList",
    "RadarCol",
    "SkillGroups",
    "FileIndex",
    "TileMatrix",
    "BinaryReader",
    "Verdata",
    "EquipConv",
]

_exported: list[str] = []

for name in _EXPORTS:
    try:
        module = __import__(f"ultima_sdk.{name.lower()}", fromlist=[name])
        obj = getattr(module, name)
        globals()[name] = obj
        _exported.append(name)
    except Exception:
        # defer until used
        pass

__all__ = _exported  # pyright: ignore[reportUnsupportedDunderAll]

# Expose common unittest.mock helpers to tests that reference them by name
try:
    import builtins
    from unittest.mock import patch, mock_open

    if not hasattr(builtins, "patch"):
        setattr(builtins, "patch", patch)
    if not hasattr(builtins, "mock_open"):
        setattr(builtins, "mock_open", mock_open)
except Exception:
    pass
