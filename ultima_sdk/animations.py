"""
Animations module - Manages creature and player animations.
"""

from __future__ import annotations

import struct
from typing import Dict, List, Optional, Tuple

from .exceptions import FileAccessException, FileParseError
from .def_files import BodyConvDef, BodyDef
from .file_index import FileIndex
from .files import Files
from .verdata_ids import IDS as VERDATA_IDS


class AnimationFrame:
    """Represents a single animation frame."""

    def __init__(
        self,
        graphic: int = 0,
        x: int = 0,
        y: int = 0,
        *,
        width: int = 0,
        height: int = 0,
        pixels: bytes = b"",
    ):
        self.graphic = graphic
        self.x_offset = x
        self.y_offset = y
        self.width = width
        self.height = height
        self.pixels = pixels


class AnimationData:
    """Represents an animation sequence."""

    def __init__(self, body_id: int, action: int, direction: int):
        self.body_id = body_id
        self.action = action
        self.direction = direction
        self.frames: List[AnimationFrame] = []


class Animations:
    """Static class for managing animation data."""

    _animations: List[AnimationData] = []
    _index_sets: Dict[int, FileIndex] = {}
    _cache: Dict[Tuple[int, int, int], AnimationData] = {}
    _initialized = False

    _body_conv: Optional[BodyConvDef] = None
    _body_def: Optional[BodyDef] = None

    # UO stores 22 actions * 5 directions per body in classic anim.mul sets.
    _ACTIONS_PER_BODY = 22
    _DIRS_PER_ACTION = 5
    _ENTRIES_PER_BODY = _ACTIONS_PER_BODY * _DIRS_PER_ACTION

    @classmethod
    def initialize(cls) -> bool:
        """Initialize animation data."""
        if cls._initialized:
            return True

        try:
            cls._index_sets = {}
            cls._cache = {}
            cls._body_conv = None
            cls._body_def = None

            # Load whichever anim sets exist under Files.
            for file_type, base in [(1, "anim"), (2, "anim2"), (3, "anim3"), (4, "anim4"), (5, "anim5")]:
                idx_path = Files.get_file_path(f"{base}.idx")
                mul_path = Files.get_file_path(f"{base}.mul")
                if not idx_path or not mul_path:
                    continue
                cls._index_sets[file_type] = FileIndex(idx_path, mul_path, file_id=VERDATA_IDS.ANIM_MUL)

            # Load .def translation tables if present.
            bodyconv_path = Files.get_file_path("bodyconv.def")
            if bodyconv_path:
                try:
                    with open(bodyconv_path, "r", encoding="utf-8", errors="ignore") as f:
                        cls._body_conv = BodyConvDef.from_text(f.read())
                except Exception:
                    cls._body_conv = None

            bodydef_path = Files.get_file_path("body.def")
            if bodydef_path:
                try:
                    with open(bodydef_path, "r", encoding="utf-8", errors="ignore") as f:
                        cls._body_def = BodyDef.from_text(f.read())
                except Exception:
                    cls._body_def = None

            cls._initialized = True
            return len(cls._index_sets) > 0
        except Exception as e:
            raise FileAccessException(f"Failed to initialize animations: {e}")

    @classmethod
    def get_animation(cls, body: int, action: int, direction: int) -> Optional[AnimationData]:
        """Get animation data."""
        if not cls._initialized:
            cls.initialize()

        if not cls._index_sets:
            return None

        # Normalize direction: classic storage is 0..4.
        if direction < 0:
            return None
        if direction >= cls._DIRS_PER_ACTION:
            direction = direction % cls._DIRS_PER_ACTION

        key = (int(body), int(action), int(direction))
        cached = cls._cache.get(key)
        if cached is not None:
            return cached

        resolved_body = cls._resolve_body_for_animation(int(body))
        file_type, converted_body = cls._resolve_anim_file_type_and_body(resolved_body)
        entry_id = cls._compute_entry_id(converted_body, int(action), int(direction))
        if entry_id < 0:
            return None

        file_index = cls._get_index_set(file_type)

        raw = file_index.read_raw(entry_id)
        if not raw:
            return None

        anim = AnimationData(body_id=int(body), action=int(action), direction=int(direction))
        try:
            anim.frames = cls._decode_animation_entry(raw)
        except FileParseError:
            raise
        except Exception as e:
            raise FileParseError("Invalid animation data", cause=e)

        cls._cache[key] = anim
        return anim

    @classmethod
    def save_gif(
        cls,
        body: int,
        action: int,
        direction: int,
        path,
        *,
        duration_ms: int = 100,
        loop: int = 0,
    ) -> bool:
        """Fetch an animation and save it as an animated GIF.

        Returns False if the animation is missing.
        """
        anim = cls.get_animation(int(body), int(action), int(direction))
        if anim is None:
            return False

        # Local import to avoid module import cycles.
        from .animation_edit import AnimationEdit

        return AnimationEdit.save_gif(anim, path, duration_ms=duration_ms, loop=loop)

    @classmethod
    def _get_index_set(cls, file_type: int) -> FileIndex:
        if not cls._index_sets:
            raise FileAccessException("Animations not initialized")

        # Prefer requested file type.
        idx = cls._index_sets.get(int(file_type))
        if idx is not None:
            return idx

        # Fall back to anim.mul if present.
        idx = cls._index_sets.get(1)
        if idx is not None:
            return idx

        # Otherwise fall back to any available set.
        return next(iter(cls._index_sets.values()))

    @classmethod
    def _resolve_body_for_animation(cls, body: int) -> int:
        if cls._body_def is None:
            return body
        try:
            return int(cls._body_def.translate_body(body))
        except Exception:
            return body

    @classmethod
    def _resolve_anim_file_type_and_body(cls, body: int) -> Tuple[int, int]:
        if cls._body_conv is None:
            return (1, body)
        try:
            res = cls._body_conv.resolve(body)
            return (int(res.file_type), int(res.body))
        except Exception:
            return (1, body)

    @classmethod
    def _compute_entry_id(cls, body: int, action: int, direction: int) -> int:
        if body < 0 or action < 0 or direction < 0:
            return -1

        # Classic client indexing is piecewise by body range and varies between
        # 22-actions (110 entries) and 13-actions (65 entries) bodies.
        if body < 200:
            base = body * 110
            actions = 22
        elif body < 400:
            base = 22000 + (body - 200) * 65
            actions = 13
        elif body < 600:
            base = 35000 + (body - 400) * 110
            actions = 22
        elif body < 800:
            base = 57000 + (body - 600) * 65
            actions = 13
        else:
            base = 70000 + (body - 800) * 110
            actions = 22

        if action >= actions:
            return -1

        # Directions are stored as 0..4.
        if direction >= cls._DIRS_PER_ACTION:
            direction = direction % cls._DIRS_PER_ACTION

        return int(base + (action * cls._DIRS_PER_ACTION) + direction)

    @classmethod
    def _decode_animation_entry(cls, data: bytes) -> List[AnimationFrame]:
        """Decode a classic UO anim.mul entry.

        Supported structure (classic MUL):
        - int32 frame_count
        - int32 frame_offsets[frame_count] (relative to start of entry)
        - frames with:
            int16 center_x, int16 center_y, int16 width, int16 height
            int32 line_offsets[height] (relative to frame start)
            scanline RLE data per line:
                (int16 x_offset, int16 run_len, uint16[run_len]) ... until (0,0)
        """
        if len(data) < 4:
            raise FileParseError("Invalid animation data")

        (frame_count,) = struct.unpack_from("<i", data, 0)
        if frame_count <= 0 or frame_count > 2048:
            raise FileParseError("Invalid animation frame count")

        offsets_base = 4
        offsets_len = frame_count * 4
        if len(data) < offsets_base + offsets_len:
            raise FileParseError("Invalid animation offsets")

        frame_offsets = list(struct.unpack_from(f"<{frame_count}i", data, offsets_base))
        frames: List[AnimationFrame] = []

        for off in frame_offsets:
            if off <= 0 or off >= len(data):
                # Some entries may have 0 offsets for empty frames.
                continue

            if len(data) < off + 8:
                raise FileParseError("Invalid animation frame header")

            center_x, center_y, width, height = struct.unpack_from("<hhhh", data, off)
            if width <= 0 or height <= 0:
                continue

            line_table_off = off + 8
            if len(data) < line_table_off + (height * 4):
                raise FileParseError("Invalid animation line table")

            line_offsets = struct.unpack_from(f"<{height}i", data, line_table_off)
            pixels = bytearray(width * height * 2)

            for y in range(height):
                line_off = int(line_offsets[y])
                if line_off <= 0:
                    continue
                p = off + line_off
                if p < 0 or p >= len(data):
                    continue

                while True:
                    if p + 4 > len(data):
                        raise FileParseError("Truncated animation RLE")

                    x_off, run_len = struct.unpack_from("<hh", data, p)
                    p += 4

                    if x_off == 0 and run_len == 0:
                        break

                    if run_len < 0:
                        raise FileParseError("Invalid animation RLE run")

                    byte_len = run_len * 2
                    if p + byte_len > len(data):
                        raise FileParseError("Truncated animation pixel run")

                    if x_off < 0 or (x_off + run_len) > width:
                        # Out-of-bounds; treat as corrupted.
                        raise FileParseError("Animation RLE out of bounds")

                    dst = ((y * width) + x_off) * 2
                    pixels[dst : dst + byte_len] = data[p : p + byte_len]
                    p += byte_len

            frames.append(
                AnimationFrame(
                    graphic=0,
                    x=int(center_x),
                    y=int(center_y),
                    width=int(width),
                    height=int(height),
                    pixels=bytes(pixels),
                )
            )

        if not frames:
            raise FileParseError("No animation frames")

        return frames
