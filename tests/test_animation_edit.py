"""Tests for AnimationEdit helpers."""

import struct

from PIL import Image

from ultima_sdk.animation_edit import AnimationEdit
from ultima_sdk.animations import AnimationData, AnimationFrame


def test_frame_to_image_uo16():
    frame = AnimationFrame(width=1, height=1, pixels=struct.pack("<H", 0x7FFF))
    img = AnimationEdit.frame_to_image(frame)
    assert isinstance(img, Image.Image)
    assert img.size == (1, 1)


def test_animation_to_images():
    anim = AnimationData(body_id=0, action=0, direction=0)
    anim.frames = [AnimationFrame(width=1, height=1, pixels=struct.pack("<H", 0x7FFF))]
    images = AnimationEdit.animation_to_images(anim)
    assert len(images) == 1
    assert images[0].size == (1, 1)
