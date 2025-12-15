"""
Sound module - Manages sound and music data.
"""

from typing import Optional, Tuple
import struct
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException, WaveFormatException


class SoundData:
    """Represents sound data."""

    def __init__(self, sound_id: int, data: bytes, name: str | None = None):
        self.sound_id = sound_id
        self.data = data
        self.name = name


class Sound:
    """Static class for managing sound data."""

    _index: Optional[object] = None
    _initialized = False

    @classmethod
    def initialize(cls, idx_path: str | None = None, mul_path: str | None = None) -> bool:
        """Initialize sound index."""
        if cls._initialized:
            return True

        try:
            if idx_path is None:
                idx_path = Files.get_file_path("soundidx.mul")
            if mul_path is None:
                mul_path = Files.get_file_path("sound.mul")

            from .verdata_ids import IDS as VERDATA_IDS

            if idx_path and mul_path:
                from .file_index import FileIndex

                cls._index = FileIndex(idx_path, mul_path, file_id=VERDATA_IDS.SOUND_MUL)
                cls._initialized = True
                return True

            # UOP fallback (newer clients).
            uop_path = Files.get_file_path("soundlegacymul.uop")
            if uop_path:
                from .uop import UopBackedIndex

                cls._index = UopBackedIndex(
                    uop_path,
                    "build/soundlegacymul/{0:D8}.dat",
                    has_extra=False,
                    file_id=VERDATA_IDS.SOUND_MUL,
                )
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize sounds: {e}")

        return False

    @classmethod
    def get_sound(cls, sound_id: int) -> Optional[SoundData]:
        """Get sound by ID."""
        if not cls._initialized:
            cls.initialize()

        if not cls._index:
            return None

        raw = cls._index.read_raw(sound_id)
        if not raw:
            return None

        name, wave = cls._coerce_to_wav(raw)

        if not cls._looks_like_wav(wave):
            raise WaveFormatException("Sound data is not a valid RIFF/WAVE stream")

        return SoundData(sound_id=sound_id, data=wave, name=name)

    @classmethod
    def _coerce_to_wav(cls, raw: bytes) -> Tuple[str | None, bytes]:
        """Return (name, wav_bytes).

        Supported inputs:
        - Raw RIFF/WAVE
        - RIFF/WAVE preceded by a fixed 40-byte name
        - UO legacy sound payloads (often name-prefixed + non-RIFF PCM)
        """

        if cls._looks_like_wav(raw):
            return (None, raw)

        # Some installs prefix sound entries with a 40-byte name.
        if len(raw) > 40 and cls._looks_like_wav(raw[40:]):
            name = cls._decode_name(raw[:40])
            return (name, raw[40:])

        # Some UOP installs store a NUL-terminated filename prefix (often ending in .wav)
        # followed by a legacy non-RIFF buffer.
        name = None
        candidates = []
        nul = raw.find(b"\x00", 0, 64)
        if nul != -1:
            # include the trailing NUL and a 2-byte aligned variant (some writers pad)
            candidates.append(nul + 1)
            candidates.append(min(len(raw), nul + 2))
        # also consider the classic fixed-size name field
        if len(raw) > 40:
            candidates.append(40)
        candidates.append(0)

        best_offset = None
        best_score = -1
        best_pcm = b""
        for off in candidates:
            if off <= 0 or off >= len(raw):
                continue
            # Parse a human-ish name only for plausible prefixes.
            prefix = raw[:off]
            decoded = cls._decode_name(prefix)
            if decoded and (".wav" in decoded.lower() or decoded.replace("_", "").isalnum()):
                name = decoded

            # Score raw[off:] as PCM, and raw[off+32:] in case there's a small header.
            for pcm_off in (off, off + 32):
                if pcm_off >= len(raw):
                    continue
                pcm = raw[pcm_off:]
                score = cls._pcm_score(pcm)
                if score > best_score:
                    best_score = score
                    best_offset = pcm_off
                    best_pcm = pcm

        # If we couldn't find a convincing PCM start, fail.
        if best_offset is None or best_score < 1:
            return (None, raw)

        wav = cls._wrap_pcm_as_wav(best_pcm)
        return (name, wav)

    @staticmethod
    def _decode_name(prefix: bytes) -> str | None:
        if not prefix:
            return None
        # Trim trailing NULs and whitespace.
        p = prefix.split(b"\x00", 1)[0].strip()
        if not p:
            return None
        try:
            s = p.decode("utf-8", errors="ignore")
        except Exception:
            return None
        s = s.strip()
        return s or None

    @staticmethod
    def _pcm_score(data: bytes) -> int:
        """Heuristic score for whether bytes look like 16-bit PCM."""
        if data is None:
            return 0
        # Need at least a small window and even length.
        if len(data) < 256:
            return 0
        if (len(data) & 1) != 0:
            data = data[:-1]

        window = data[:512]
        # Interpret as signed 16-bit little-endian.
        sample_count = len(window) // 2
        try:
            samples = struct.unpack_from(f"<{sample_count}h", window, 0)
        except Exception:
            return 0

        # Reject if it's almost all zeros or almost all one value.
        unique = len(set(samples))
        if unique <= 2:
            return 0
        # Clamp extremes: typical audio has most samples not pegged at +/-32768.
        clipped = sum(1 for x in samples if abs(x) >= 32000)
        if clipped > sample_count * 0.25:
            return 0
        # Favor higher entropy.
        return unique

    @staticmethod
    def _wrap_pcm_as_wav(pcm: bytes, *, sample_rate: int = 22050, channels: int = 1, bits_per_sample: int = 16) -> bytes:
        """Wrap raw PCM bytes as a minimal RIFF/WAVE container."""
        if pcm is None:
            pcm = b""

        # Ensure block alignment.
        block_align = channels * (bits_per_sample // 8)
        if block_align <= 0:
            block_align = 2

        if len(pcm) % block_align != 0:
            pcm = pcm[: len(pcm) - (len(pcm) % block_align)]

        byte_rate = sample_rate * block_align
        fmt = (
            b"fmt "
            + struct.pack("<I", 16)
            + struct.pack("<HHIIHH", 1, channels, sample_rate, byte_rate, block_align, bits_per_sample)
        )
        data = b"data" + struct.pack("<I", len(pcm)) + pcm
        riff_payload = b"WAVE" + fmt + data
        return b"RIFF" + struct.pack("<I", len(riff_payload)) + riff_payload

    @staticmethod
    def _looks_like_wav(data: bytes) -> bool:
        # Minimal RIFF/WAVE validation.
        if len(data) < 12:
            return False
        if data[0:4] != b"RIFF":
            return False
        if data[8:12] != b"WAVE":
            return False

        # If the RIFF chunk size is present and plausible, accept.
        # RIFF size excludes the leading 'RIFF' + size field (8 bytes).
        try:
            riff_size = int.from_bytes(data[4:8], "little", signed=False)
        except Exception:
            return False

        # Some writers use 0 or don't match exactly; be permissive but reject absurd values.
        if riff_size > (1024 * 1024 * 256):
            return False

        return True
