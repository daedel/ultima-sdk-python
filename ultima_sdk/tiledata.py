"""
TileData module - Manages tile properties and static item data.
Supports full read AND write (patch individual tiles + save whole file).
"""

import struct
from typing import List, Optional, Dict
from .binary_extensions import BinaryReader
from .files import Files
from .exceptions import FileAccessException


class TileFlag:
    """Flags for tile properties."""

    NONE = 0x00000000
    BACKGROUND = 0x00000001
    WEAPON = 0x00000002
    TRANSPARENT = 0x00000004
    TRANSLUCENT = 0x00000008
    WALL = 0x00000010
    DAMAGING = 0x00000020
    IMPASSABLE = 0x00000040
    WET = 0x00000080
    UNKNOWN1 = 0x00000100
    SURFACE = 0x00000200
    BRIDGE = 0x00000400
    STACKABLE = 0x00000800
    WINDOW = 0x00001000
    NO_SHOOT = 0x00002000
    ARTICULATED = 0x00004000
    FOLIAGE = 0x00008000
    PARTIAL_HUE = 0x00010000
    UNKNOWN2 = 0x00020000
    MAP = 0x00040000
    CONTAINER = 0x00080000
    WEARABLE = 0x00100000
    LIGHT_SOURCE = 0x00200000
    ANIMATED = 0x00400000
    HOVEROVER = 0x00800000
    UNKNOWN3 = 0x01000000
    ARMOR = 0x02000000
    ROOF = 0x04000000
    DOOR = 0x08000000
    STAIRS = 0x10000000
    LAVA = 0x20000000
    UNKNOWN4 = 0x40000000
    UNKNOWNX = 0x80000000


# Byte sizes for the two entry formats.
_LAND_ENTRY_SIZE = 26  # uint32 flags + uint16 texture_id + 20-byte name
_ITEM_ENTRY_SIZE = 37  # uint32 flags + byte weight + byte quality + uint16 quantity
# + uint16 value + byte height + 20-byte name
# tiledata.mul layout:
#   512 land-tile header groups * (4-byte group header + 32 * 26-byte entries)
#   512 item-tile header groups * (4-byte group header + 32 * 37-byte entries)
_LAND_GROUP_ENTRIES = 32
_ITEM_GROUP_ENTRIES = 32
_LAND_GROUPS = 512
_ITEM_GROUPS = 512


class TileData:
    """Static class for managing tile data."""

    _land_tiles: List[Dict] = []
    _item_tiles: List[Dict] = []
    _initialized = False

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    @classmethod
    def initialize(cls) -> bool:
        """Load tile data from file."""
        if cls._initialized:
            return True
        try:
            path = Files.get_file_path("tiledata.mul")
            if not path:
                return False
            with open(path, "rb") as f:
                reader = BinaryReader(f)
                cls._load_tiledata(reader)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to load tiledata.mul: {e}")

    @classmethod
    def _load_tiledata(cls, reader: BinaryReader) -> None:
        """Load all tile data from reader."""
        cls._land_tiles = []
        for _group in range(_LAND_GROUPS):
            reader.read_uint32()  # group header (unused)
            for _ in range(_LAND_GROUP_ENTRIES):
                cls._land_tiles.append(cls._read_land_tile_entry(reader))

        cls._item_tiles = []
        for _group in range(_ITEM_GROUPS):
            reader.read_uint32()  # group header (unused)
            for _ in range(_ITEM_GROUP_ENTRIES):
                cls._item_tiles.append(cls._read_item_tile_entry(reader))

    @staticmethod
    def _read_land_tile_entry(reader: BinaryReader) -> Dict:
        return {
            "flags": reader.read_uint32(),
            "texture_id": reader.read_uint16(),
            "name": reader.read_string(20, null_terminated=True).strip("\x00"),
        }

    @staticmethod
    def _read_item_tile_entry(reader: BinaryReader) -> Dict:
        return {
            "flags": reader.read_uint32(),
            "weight": reader.read_byte(),
            "quality": reader.read_byte(),
            "quantity": reader.read_uint16(),
            "value": reader.read_uint16(),
            "height": reader.read_byte(),
            "name": reader.read_string(20, null_terminated=True).strip("\x00"),
        }

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @classmethod
    def get_land_tile(cls, id: int) -> Optional[Dict]:
        if not cls._initialized:
            cls.initialize()
        if 0 <= id < len(cls._land_tiles):
            return cls._land_tiles[id]
        return None

    @classmethod
    def get_item_tile(cls, id: int) -> Optional[Dict]:
        if not cls._initialized:
            cls.initialize()
        if 0 <= id < len(cls._item_tiles):
            return cls._item_tiles[id]
        return None

    # ------------------------------------------------------------------
    # In-memory patch
    # ------------------------------------------------------------------

    @classmethod
    def set_land_tile(cls, id: int, **fields) -> None:
        """Patch one or more fields on a land tile entry (in memory).

        Recognised keys: ``flags``, ``texture_id``, ``name``.
        Call :meth:`save` to persist changes.
        """
        if not cls._initialized:
            cls.initialize()
        if not (0 <= id < len(cls._land_tiles)):
            raise IndexError(f"Land tile id {id} out of range")
        entry = dict(cls._land_tiles[id])
        for k, v in fields.items():
            if k not in entry:
                raise KeyError(f"Unknown land tile field: {k!r}")
            entry[k] = v
        cls._land_tiles[id] = entry

    @classmethod
    def set_item_tile(cls, id: int, **fields) -> None:
        """Patch one or more fields on an item tile entry (in memory).

        Recognised keys: ``flags``, ``weight``, ``quality``, ``quantity``,
        ``value``, ``height``, ``name``.
        Call :meth:`save` to persist changes.
        """
        if not cls._initialized:
            cls.initialize()
        if not (0 <= id < len(cls._item_tiles)):
            raise IndexError(f"Item tile id {id} out of range")
        entry = dict(cls._item_tiles[id])
        for k, v in fields.items():
            if k not in entry:
                raise KeyError(f"Unknown item tile field: {k!r}")
            entry[k] = v
        cls._item_tiles[id] = entry

    # ------------------------------------------------------------------
    # Serialise helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pack_name(name: str, length: int = 20) -> bytes:
        encoded = name.encode("latin-1", errors="replace")[:length]
        return encoded.ljust(length, b"\x00")

    @classmethod
    def _encode_land_entry(cls, entry: Dict) -> bytes:
        return struct.pack("<IH", entry["flags"], entry["texture_id"]) + cls._pack_name(
            entry["name"]
        )

    @classmethod
    def _encode_item_entry(cls, entry: Dict) -> bytes:
        return (
            struct.pack(
                "<IBBHH",
                entry["flags"],
                entry["weight"],
                entry["quality"],
                entry["quantity"],
                entry["value"],
            )
            + struct.pack("<B", entry["height"])
            + cls._pack_name(entry["name"])
        )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    @classmethod
    def save(cls, path: str | None = None) -> None:
        """Write the full tiledata.mul to *path*.

        If *path* is ``None``, overwrites the original file returned by
        :func:`Files.get_file_path("tiledata.mul")`.
        """
        if not cls._initialized:
            cls.initialize()

        if path is None:
            path = Files.get_file_path("tiledata.mul")
        if not path:
            raise FileAccessException("No tiledata.mul path available")

        with open(path, "wb") as f:
            # Land groups
            for g in range(_LAND_GROUPS):
                f.write(struct.pack("<I", 0))  # group header
                for i in range(_LAND_GROUP_ENTRIES):
                    idx = g * _LAND_GROUP_ENTRIES + i
                    f.write(cls._encode_land_entry(cls._land_tiles[idx]))

            # Item groups
            for g in range(_ITEM_GROUPS):
                f.write(struct.pack("<I", 0))  # group header
                for i in range(_ITEM_GROUP_ENTRIES):
                    idx = g * _ITEM_GROUP_ENTRIES + i
                    f.write(cls._encode_item_entry(cls._item_tiles[idx]))
