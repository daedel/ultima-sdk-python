"""
TileData module - Manages tile properties and static item data.
"""

from typing import List, Optional, Dict
from .binary_extensions import BinaryReader
from .files import Files
from .exceptions import FileAccessException, InvalidFormatException


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


class TileData:
    """Static class for managing tile data."""

    _land_tiles: List = []
    _item_tiles: List = []
    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """Load tile data from file."""
        if cls._initialized:
            return True

        try:
            path = Files.get_file_path("tiledata.mul")
            if not path:
                return False

            with open(path, 'rb') as f:
                reader = BinaryReader(f)
                cls._load_tiledata(reader)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to load tiledata.mul: {e}")

    @classmethod
    def _load_tiledata(cls, reader: BinaryReader) -> None:
        """Load all tile data from reader."""
        # Land tiles (0-16383)
        cls._land_tiles = [cls._read_land_tile_entry(reader) for _ in range(16384)]

        # Item tiles (0-16383)
        cls._item_tiles = [cls._read_item_tile_entry(reader) for _ in range(16384)]

    @staticmethod
    def _read_land_tile_entry(reader: BinaryReader) -> Dict:
        """Read a single land tile entry."""
        return {
            'flags': reader.read_uint32(),
            'texture_id': reader.read_uint16(),
            'name': reader.read_string(20, null_terminated=True).strip('\x00'),
        }

    @staticmethod
    def _read_item_tile_entry(reader: BinaryReader) -> Dict:
        """Read a single item tile entry."""
        return {
            'flags': reader.read_uint32(),
            'weight': reader.read_byte(),
            'quality': reader.read_byte(),
            'quantity': reader.read_uint16(),
            'value': reader.read_uint16(),
            'height': reader.read_byte(),
            'name': reader.read_string(20, null_terminated=True).strip('\x00'),
        }

    @classmethod
    def get_land_tile(cls, id: int) -> Optional[Dict]:
        """Get land tile data by ID."""
        if not cls._initialized:
            cls.initialize()

        if 0 <= id < len(cls._land_tiles):
            return cls._land_tiles[id]
        return None

    @classmethod
    def get_item_tile(cls, id: int) -> Optional[Dict]:
        """Get item tile data by ID."""
        if not cls._initialized:
            cls.initialize()

        if 0 <= id < len(cls._item_tiles):
            return cls._item_tiles[id]
        return None
