from __future__ import annotations

from pathlib import Path

import pytest

from ultima_sdk.art import Art
from ultima_sdk.gumps import Gumps
from ultima_sdk.light import Light
from ultima_sdk.textures import Textures


class _FakeImage:
    def __init__(self):
        self.saved = []

    def save(self, path, format=None, **kwargs):
        self.saved.append((str(path), format))


class _FakeData:
    def __init__(self, img: _FakeImage):
        self._img = img

    def to_image(self):
        return self._img


def test_art_save_png_calls_image_save(monkeypatch, tmp_path):
    img = _FakeImage()

    def fake_get_art(_gid: int):
        return _FakeData(img)

    monkeypatch.setattr(Art, "get_art", staticmethod(fake_get_art))

    out = tmp_path / "a.png"
    assert Art.save_png(123, out) is True
    assert img.saved == [(str(out), "PNG")]


def test_art_save_png_uses_get_equipped_art_when_body_id(monkeypatch, tmp_path):
    img = _FakeImage()
    called = {"equipped": False}

    def fake_get_equipped(_gid: int, *, body_id=None):
        called["equipped"] = True
        assert body_id == 400
        return _FakeData(img)

    monkeypatch.setattr(Art, "get_equipped_art", staticmethod(fake_get_equipped))

    out = tmp_path / "eq.png"
    assert Art.save_png(1, out, body_id=400) is True
    assert called["equipped"] is True


def test_gumps_save_png_calls_image_save(monkeypatch, tmp_path):
    img = _FakeImage()

    def fake_get_gump(_gid: int):
        return _FakeData(img)

    monkeypatch.setattr(Gumps, "get_gump", staticmethod(fake_get_gump))

    out = tmp_path / "g.png"
    assert Gumps.save_png(1, out) is True
    assert img.saved == [(str(out), "PNG")]


def test_textures_save_png_calls_image_save(monkeypatch, tmp_path):
    img = _FakeImage()

    def fake_get_tex(_gid: int):
        return _FakeData(img)

    monkeypatch.setattr(Textures, "get_texture", staticmethod(fake_get_tex))

    out = tmp_path / "t.png"
    assert Textures.save_png(1, Path(out)) is True
    assert img.saved == [(str(out), "PNG")]


def test_light_save_png_calls_image_save(monkeypatch, tmp_path):
    img = _FakeImage()

    def fake_get_light(_gid: int):
        return _FakeData(img)

    monkeypatch.setattr(Light, "get_light", staticmethod(fake_get_light))

    out = tmp_path / "l.png"
    assert Light.save_png(1, out) is True
    assert img.saved == [(str(out), "PNG")]


@pytest.mark.parametrize(
    "func",
    [
        lambda: Art.save_png(1, 123),
        lambda: Gumps.save_png(1, 123),
        lambda: Textures.save_png(1, 123),
        lambda: Light.save_png(1, 123),
    ],
)
def test_save_png_invalid_path_raises(func):
    with pytest.raises(Exception):
        func()
