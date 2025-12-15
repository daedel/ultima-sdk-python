from __future__ import annotations

import pytest
from typing import Any

from ultima_sdk.animation_edit import AnimationEdit
from ultima_sdk.animations import Animations


class _FakeImage:
    def __init__(self):
        self.calls = []

    def save(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class _FakeAnimation:
    def __init__(self, frames_present: bool = True):
        self.frames = [object()] if frames_present else []


def test_save_gif_returns_false_for_none_or_empty(tmp_path):
    assert AnimationEdit.save_gif(None, tmp_path / "a.gif") is False
    assert AnimationEdit.save_gif(_FakeAnimation(frames_present=False), tmp_path / "b.gif") is False  # type: ignore[arg-type]


def test_save_gif_calls_pillow_save(monkeypatch, tmp_path):
    img0 = _FakeImage()
    img1 = _FakeImage()

    def fake_animation_to_images(_anim):
        return [img0, img1]

    monkeypatch.setattr(AnimationEdit, "animation_to_images", staticmethod(fake_animation_to_images))

    out = tmp_path / "anim.gif"
    anim: Any = _FakeAnimation(frames_present=True)
    assert AnimationEdit.save_gif(anim, out, duration_ms=123, loop=7) is True

    assert len(img0.calls) == 1
    (args, kwargs) = img0.calls[0]
    assert args[0] == str(out)
    assert kwargs["format"] == "GIF"
    assert kwargs["save_all"] is True
    assert kwargs["append_images"] == [img1]
    assert kwargs["duration"] == 123
    assert kwargs["loop"] == 7


def test_save_gif_invalid_path_raises():
    with pytest.raises(Exception):
        AnimationEdit.save_gif(_FakeAnimation(frames_present=True), 123)  # type: ignore[arg-type]


def test_animations_save_gif_returns_false_when_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(Animations, "get_animation", staticmethod(lambda *_a, **_k: None))
    assert Animations.save_gif(0, 0, 0, tmp_path / "x.gif") is False


def test_animations_save_gif_delegates_to_animation_edit(monkeypatch, tmp_path):
    fake_anim = object()
    monkeypatch.setattr(Animations, "get_animation", staticmethod(lambda *_a, **_k: fake_anim))

    called = {}

    def fake_save_gif(anim, path, *, duration_ms=0, loop=0):
        called["anim"] = anim
        called["path"] = str(path)
        called["duration_ms"] = duration_ms
        called["loop"] = loop
        return True

    monkeypatch.setattr(AnimationEdit, "save_gif", staticmethod(fake_save_gif))

    out = tmp_path / "anim.gif"
    assert Animations.save_gif(1, 2, 3, out, duration_ms=123, loop=7) is True
    assert called == {
        "anim": fake_anim,
        "path": str(out),
        "duration_ms": 123,
        "loop": 7,
    }
