"""Ultima Online SDK package initializer.

Expose common classes at package level for convenience.
Light/guarded imports keep import-time cost low.
"""
__version__ = "1.0.0"
__author__ = "UltimaWorks"

# Eagerly expose common high-level classes if available; keep failures silent
_EXPORTS = [
    'Files', 'TileData', 'Hues', 'Art', 'Animations', 'Gumps', 'Sound', 'Light',
    'Textures', 'Multis', 'Map', 'Skills', 'AnimationEdit', 'StringList',
    'RadarCol', 'SkillGroups', 'FileIndex', 'TileMatrix', 'BinaryReader'
]

__all__ = []

for name in _EXPORTS:
    try:
        module = __import__(f"ultima_sdk.{name.lower()}", fromlist=[name])
        obj = getattr(module, name)
        globals()[name] = obj
        __all__.append(name)
    except Exception:
        # defer until used
        pass
