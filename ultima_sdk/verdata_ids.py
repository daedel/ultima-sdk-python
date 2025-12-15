"""Known `verdata.mul` file-id mappings.

These IDs are the conventional mapping used by the legacy Ultima SDK
implementations (e.g. ServUO / Ultima SDK).

Reference (comment block): ServUO `Ultima/Verdata.cs`.

Note: Some resources (e.g. `light.mul`) do not have a known verdata file id in
this mapping.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerdataFileIds:
    # Maps / statics
    MAP0_MUL: int = 0
    STAIDX0_MUL: int = 1
    STATICS0_MUL: int = 2

    # Art
    ARTIDX_MUL: int = 3
    ART_MUL: int = 4

    # Animations
    ANIM_IDX: int = 5
    ANIM_MUL: int = 6

    # Sound
    SOUNDIDX_MUL: int = 7
    SOUND_MUL: int = 8

    # Textures
    TEXIDX_MUL: int = 9
    TEXMAPS_MUL: int = 10

    # Gumps
    GUMPIDX_MUL: int = 11
    GUMPART_MUL: int = 12

    # Multis
    MULTI_IDX: int = 13
    MULTI_MUL: int = 14

    # Skills
    SKILLS_IDX: int = 15
    SKILLS_MUL: int = 16

    # Misc
    TILEDATA_MUL: int = 30
    ANIMDATA_MUL: int = 31


IDS = VerdataFileIds()
