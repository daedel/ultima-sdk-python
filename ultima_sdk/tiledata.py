"""
TileData module - Manages tile properties and static item data.
Supports full read AND write (patch individual tiles + save whole file).

Item tile entry layout (OldItemTileDataMul, Pack=1) — 37 bytes:
  Offset  Field           C# Type     Python
  0       flags           int32       uint32
  4       weight          byte        uint8
  5       quality         byte        uint8
  6       miscdata        short       int16
  8       unk2            byte        uint8
  9       quantity        byte        uint8
  10      anim            short       int16
  12      unk3            byte        uint8
  13      hue             byte        uint8
  14      stackingoffset  byte        uint8
  15      value           byte        uint8
  16      height          byte        uint8
  17-36   name            char[20]

High Seas (NewItemTileDataMul) adds int32 unk1 after flags → 41 bytes.
Land tile old = 26 bytes; land tile HS = 30 bytes (adds int32 unk1 after flags).
"""

import os
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


# Entry sizes
_LAND_ENTRY_SIZE_OLD = 26   # flags(4) + texture_id(2) + name(20)
_LAND_ENTRY_SIZE_HS  = 30   # adds unk1(4) after flags
_ITEM_ENTRY_SIZE_OLD = 37   # canonical OldItemTileDataMul
_ITEM_ENTRY_SIZE_HS  = 41   # NewItemTileDataMul — adds unk1(4) after flags

_LAND_GROUP_ENTRIES = 32
_ITEM_GROUP_ENTRIES = 32
_LAND_GROUPS = 512
_ITEM_GROUPS = 512

# Expected file size in old format
_OLD_FILE_SIZE = (
    _LAND_GROUPS * (4 + _LAND_GROUP_ENTRIES * _LAND_ENTRY_SIZE_OLD)
    + _ITEM_GROUPS * (4 + _ITEM_GROUP_ENTRIES * _ITEM_ENTRY_SIZE_OLD)
)


class TileData:
    """Static class for managing tile data."""

    _land_tiles: List[Dict] = []
    _item_tiles: List[Dict] = []
    _initialized = False
    _uoahs: bool = False   # True when High Seas (41-byte item entries)

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
            file_size = os.path.getsize(path)
            cls._uoahs = cls._detect_uoahs(file_size)
            with open(path, "rb") as f:
                reader = BinaryReader(f)
                cls._load_tiledata(reader)
            cls._initialized = True
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to load tiledata.mul: {e}")

    @staticmethod
    def _detect_uoahs(file_size: int) -> bool:
        """Return True if file size matches the High Seas (41-byte item) layout."""
        hs_size = (
            _LAND_GROUPS * (4 + _LAND_GROUP_ENTRIES * _LAND_ENTRY_SIZE_HS)
            + _ITEM_GROUPS * (4 + _ITEM_GROUP_ENTRIES * _ITEM_ENTRY_SIZE_HS)
        )
        return file_size == hs_size

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

    @classmethod
    def _read_land_tile_entry(cls, reader: BinaryReader) -> Dict:
        flags = reader.read_uint32()
        if cls._uoahs:
            reader.read_uint32()  # unk1 — HS only
        return {
            "flags": flags,
            "texture_id": reader.read_uint16(),
            "name": reader.read_string(20, null_terminated=True).strip("\x00"),
        }

    @classmethod
    def _read_item_tile_entry(cls, reader: BinaryReader) -> Dict:
        """Read one item tile entry matching OldItemTileDataMul (37 bytes).

        High Seas (NewItemTileDataMul, 41 bytes) adds int32 unk1 after flags.
        All fields are read in canonical C# struct order.
        """
        flags    = reader.read_uint32()          # 4
        if cls._uoahs:
            reader.read_uint32()                 # unk1 — HS only, 4 bytes
        weight   = reader.read_byte()            # 1
        quality  = reader.read_byte()            # 1
        miscdata = reader.read_int16()           # 2  (short)
        unk2     = reader.read_byte()            # 1
        quantity = reader.read_byte()            # 1
        anim     = reader.read_int16()           # 2  (short)
        unk3     = reader.read_byte()            # 1
        hue      = reader.read_byte()            # 1
        stacking = reader.read_byte()            # 1
        value    = reader.read_byte()            # 1
        height   = reader.read_byte()            # 1
        name     = reader.read_string(20, null_terminated=True).strip("\x00")  # 20
        # Total old: 4+1+1+2+1+1+2+1+1+1+1+1+20 = 37 bytes ✓
        # Total HS:  4+4+1+1+2+1+1+2+1+1+1+1+1+20 = 41 bytes ✓
        return {
            "flags":    flags,
            "weight":   weight,
            "quality":  quality,
            "miscdata": miscdata,
            "unk2":     unk2,
            "quantity": quantity,
            "anim":     anim,
            "unk3":     unk3,
            "hue":      hue,
            "stackingoffset": stacking,
            "value":    value,
            "height":   height,
            "name":     name,
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

        Recognised keys: ``flags``, ``weight``, ``quality``, ``miscdata``,
        ``unk2``, ``quantity``, ``anim``, ``unk3``, ``hue``,
        ``stackingoffset``, ``value``, ``height``, ``name``.
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
        """Encode one item tile entry back to the 37-byte OldItemTileDataMul layout.

        Field order matches the C# struct exactly — unknown fields are preserved
        where present in the dict, otherwise written as zero.
        """
        return (
            struct.pack(
                "<IBBhBBhBBBBB",
                entry["flags"],
                entry["weight"],
                entry["quality"],
                entry.get("miscdata", 0),
                entry.get("unk2", 0),
                entry["quantity"],
                entry.get("anim", 0),
                entry.get("unk3", 0),
                entry.get("hue", 0),
                entry.get("stackingoffset", 0),
                entry["value"],
                entry["height"],
            )
            + cls._pack_name(entry["name"])
        )
        # struct layout breakdown:
        # I=flags(4) B=weight(1) B=quality(1) h=miscdata(2) B=unk2(1)
        # B=quantity(1) h=anim(2) B=unk3(1) B=hue(1) B=stacking(1)
        # B=value(1) B=height(1) → 17 bytes + name(20) = 37 bytes ✓

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    @classmethod
    def save(cls, path: str | None = None) -> None:
        """Write the full tiledata.mul to *path*.

        If *path* is ``None``, overwrites the original file returned by
        :func:`Files.get_file_path("tiledata.mul")`.

        Note: always saves in OldItemTileDataMul (37-byte) format regardless
        of whether the source was High Seas — UOAHS write support is a TODO.
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

    # ------------------------------------------------------------------
    # Verdata patch integration
    # ------------------------------------------------------------------

    @classmethod
    def apply_verdata_patch(cls, block_id: int, data: bytes, extra: int = 0) -> None:
        """Apply a raw verdata.mul patch to the in-memory tile cache.

        block_id maps directly to a tile index:
          - block_id < 0x4000  -> land tile  (block_id itself is the tile id)
          - block_id >= 0x4000 -> item tile  (block_id - 0x4000 is the tile id)

        data must be exactly _LAND_ENTRY_SIZE_OLD/HS or _ITEM_ENTRY_SIZE_OLD/HS
        bytes -- the raw struct as it appears in tiledata.mul, matching whatever
        format was detected at initialize() time.

        extra is unused for tiledata patches but kept for API consistency.
        """
        if not cls._initialized:
            cls.initialize()

        import io
        reader = BinaryReader(io.BytesIO(data))

        if block_id < 0x4000:
            # Land tile
            tile_id = block_id
            if not (0 <= tile_id < len(cls._land_tiles)):
                return
            cls._land_tiles[tile_id] = cls._read_land_tile_entry(reader)
        else:
            # Item tile
            tile_id = block_id - 0x4000
            if not (0 <= tile_id < len(cls._item_tiles)):
                return
            cls._item_tiles[tile_id] = cls._read_item_tile_entry(reader)
