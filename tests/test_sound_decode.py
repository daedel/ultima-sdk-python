"""Tests for sound decoding via idx/mul bytes.

These tests do not require an installed Ultima Online client.
"""

from __future__ import annotations

import struct

import pytest

from ultima_sdk.sound import Sound
from ultima_sdk.exceptions import WaveFormatException


def _minimal_wav_bytes() -> bytes:
    # Create a minimal (but valid enough) RIFF/WAVE file:
    # RIFF + size + WAVE + fmt chunk + data chunk.
    fmt_chunk = (
        b"fmt "
        + struct.pack("<I", 16)  # fmt chunk size
        + struct.pack("<HHIIHH", 1, 1, 8000, 8000 * 2, 2, 16)  # PCM mono 16-bit
    )
    data_chunk = b"data" + struct.pack("<I", 2) + b"\x00\x00"

    riff_payload = b"WAVE" + fmt_chunk + data_chunk
    riff = b"RIFF" + struct.pack("<I", len(riff_payload)) + riff_payload
    return riff


def test_sound_get_sound_reads_idx_mul_wav(tmp_path):
    wav = _minimal_wav_bytes()

    mul_path = tmp_path / "sound.mul"
    mul_path.write_bytes(wav)

    idx_path = tmp_path / "soundidx.mul"
    idx_path.write_bytes(struct.pack("<iii", 0, len(wav), 0))

    Sound._initialized = False
    Sound._index = None
    assert Sound.initialize(str(idx_path), str(mul_path)) is True

    s = Sound.get_sound(0)
    assert s is not None
    assert s.data[:4] == b"RIFF"
    assert s.data[8:12] == b"WAVE"


def test_sound_get_sound_raises_on_non_wav(tmp_path):
    raw = b"NOTWAV" * 10

    mul_path = tmp_path / "sound.mul"
    mul_path.write_bytes(raw)

    idx_path = tmp_path / "soundidx.mul"
    idx_path.write_bytes(struct.pack("<iii", 0, len(raw), 0))

    Sound._initialized = False
    Sound._index = None
    assert Sound.initialize(str(idx_path), str(mul_path)) is True

    with pytest.raises(WaveFormatException):
        Sound.get_sound(0)


def test_sound_get_sound_wraps_legacy_pcm_into_wav(tmp_path):
    # Simulate an installed-client legacy sound payload:
    # NUL-terminated filename prefix + (optional) small header + raw 16-bit PCM.
    name = b"d_frst01.wav\x00"
    legacy_header = b"\x00" * 32

    # Build PCM samples with enough variation to look like audio.
    samples = [((i * 97) % 2000) - 1000 for i in range(2048)]
    pcm = struct.pack("<%dh" % len(samples), *samples)
    raw = name + legacy_header + pcm

    mul_path = tmp_path / "sound.mul"
    mul_path.write_bytes(raw)

    idx_path = tmp_path / "soundidx.mul"
    idx_path.write_bytes(struct.pack("<iii", 0, len(raw), 0))

    Sound._initialized = False
    Sound._index = None
    assert Sound.initialize(str(idx_path), str(mul_path)) is True

    s = Sound.get_sound(0)
    assert s is not None
    assert s.data[:4] == b"RIFF"
    assert s.data[8:12] == b"WAVE"
    assert s.name == "d_frst01.wav"
