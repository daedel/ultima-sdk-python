"""UOP container support.

Ultima Online "*.uop" files are container archives used by newer client installs.
This module implements the subset needed by the SDK:

- Parse UOP header and blocks
- Map entry hash -> entry metadata
- Recreate ClassicUO-compatible hash function
- Read and (optionally) decompress entry bytes

The UOP format relies on hashing a virtual filename (derived from a pattern)
into a 64-bit value, then using that hash to locate the payload.

Patterns in the community are typically expressed using C#-style formatting
like "build/artlegacymul/{0:D8}.tga".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
import re
import struct
import zlib


_UOP_MAGIC = 0x50594D  # 'MYP'


class UopError(Exception):
    pass


class UopFormatError(UopError):
    pass


class UopCompressionError(UopError):
    pass


@dataclass(frozen=True)
class UopEntry:
    offset: int
    compressed_length: int
    decompressed_length: int
    compression_flag: int
    extra1: int = 0
    extra2: int = 0


_CSHARP_FMT_RE = re.compile(r"\{(\d+)(?::D(\d+))?\}")


def _format_csharp_pattern(pattern: str, *args: int) -> str:
    """Format a C#-style pattern like ".../{0:D8}.dat" with integer args."""

    def repl(match: re.Match) -> str:
        idx = int(match.group(1))
        width = match.group(2)
        if idx >= len(args):
            raise ValueError(f"Pattern placeholder {{{idx}}} out of range")
        value = int(args[idx])
        if width is None:
            return str(value)
        return f"{value:0{int(width)}d}"

    return _CSHARP_FMT_RE.sub(repl, pattern)


def _u32(x: int) -> int:
    return x & 0xFFFFFFFF


def create_hash(s: str) -> int:
    """Compute the 64-bit UOP hash for a virtual filename.

    This is a direct port of the widely-used UOP hashing routine (as used by
    ClassicUO and other tools) for ASCII-ish paths.

    Returns:
        Unsigned 64-bit hash as Python int.
    """

    # Use latin-1 so bytes map 1:1 for 0-255; UOP virtual filenames are ASCII.
    b = s.encode("latin-1")

    eax = ecx = edx = ebx = esi = edi = 0
    ebx = edi = esi = _u32(len(b) + 0xDEADBEEF)

    i = 0
    while i + 12 < len(b):
        edi = _u32(((b[i + 7] << 24) | (b[i + 6] << 16) | (b[i + 5] << 8) | b[i + 4]) + edi)
        esi = _u32(((b[i + 11] << 24) | (b[i + 10] << 16) | (b[i + 9] << 8) | b[i + 8]) + esi)
        edx = _u32(((b[i + 3] << 24) | (b[i + 2] << 16) | (b[i + 1] << 8) | b[i]) - esi)

        edx = _u32((edx + ebx) ^ (esi >> 28) ^ _u32(esi << 4))
        esi = _u32(esi + edi)
        edi = _u32((edi - edx) ^ (edx >> 26) ^ _u32(edx << 6))
        edx = _u32(edx + esi)
        esi = _u32((esi - edi) ^ (edi >> 24) ^ _u32(edi << 8))
        edi = _u32(edi + edx)
        ebx = _u32((edx - esi) ^ (esi >> 16) ^ _u32(esi << 16))
        esi = _u32(esi + edi)
        edi = _u32((edi - ebx) ^ (ebx >> 13) ^ _u32(ebx << 19))
        ebx = _u32(ebx + esi)
        esi = _u32((esi - edi) ^ (edi >> 28) ^ _u32(edi << 4))
        edi = _u32(edi + ebx)

        i += 12

    if len(b) - i > 0:
        remain = len(b) - i

        if remain >= 12:
            esi = _u32(esi + (b[i + 11] << 24))
        if remain >= 11:
            esi = _u32(esi + (b[i + 10] << 16))
        if remain >= 10:
            esi = _u32(esi + (b[i + 9] << 8))
        if remain >= 9:
            esi = _u32(esi + b[i + 8])

        if remain >= 8:
            edi = _u32(edi + (b[i + 7] << 24))
        if remain >= 7:
            edi = _u32(edi + (b[i + 6] << 16))
        if remain >= 6:
            edi = _u32(edi + (b[i + 5] << 8))
        if remain >= 5:
            edi = _u32(edi + b[i + 4])

        if remain >= 4:
            ebx = _u32(ebx + (b[i + 3] << 24))
        if remain >= 3:
            ebx = _u32(ebx + (b[i + 2] << 16))
        if remain >= 2:
            ebx = _u32(ebx + (b[i + 1] << 8))
        if remain >= 1:
            ebx = _u32(ebx + b[i])

    edx = _u32((esi ^ edi) - ((edi >> 18) ^ _u32(edi << 14)))
    ecx = _u32((edx ^ ebx) - ((edx >> 21) ^ _u32(edx << 11)))
    edi = _u32((edi ^ ecx) - ((ecx >> 7) ^ _u32(ecx << 25)))
    edx = _u32((edx ^ edi) - ((edi >> 16) ^ _u32(edi << 16)))
    eax = _u32((ecx ^ edx) - ((edx >> 28) ^ _u32(edx << 4)))
    edi = _u32((edi ^ eax) - ((eax >> 18) ^ _u32(eax << 14)))
    eax = _u32((edx ^ edi) - ((edi >> 8) ^ _u32(edi << 24)))

    return (_u32(edi) << 32) | _u32(eax)


def _decompress(flag: int, payload: bytes, decompressed_length: int) -> bytes:
    if flag == 0:
        return payload

    if flag == 1:
        try:
            out = zlib.decompress(payload)
        except zlib.error:
            # Some tools store raw DEFLATE streams.
            try:
                out = zlib.decompress(payload, -15)
            except zlib.error as e:
                raise UopCompressionError(f"zlib decompression failed: {e}") from e

        if decompressed_length > 0 and len(out) != decompressed_length:
            # Be permissive: some headers are off, but keep a sanity limit.
            if abs(len(out) - decompressed_length) > 16:
                raise UopCompressionError(
                    f"Decompressed length mismatch: expected {decompressed_length}, got {len(out)}"
                )
        return out

    if flag == 3:
        # Classic client assets sometimes store an additional BWT/MTF stage after zlib.
        # The UOP entry's decompressed_length refers to the zlib output length.
        try:
            out = zlib.decompress(payload)
        except zlib.error:
            try:
                out = zlib.decompress(payload, -15)
            except zlib.error as e:
                raise UopCompressionError(f"zlib decompression failed: {e}") from e

        if decompressed_length > 0 and len(out) != decompressed_length:
            if abs(len(out) - decompressed_length) > 16:
                raise UopCompressionError(
                    f"Decompressed length mismatch: expected {decompressed_length}, got {len(out)}"
                )

        return _bwt_decompress(out)

    raise UopCompressionError(f"Unsupported UOP compression flag: {flag}")


def _bwt_decompress(buffer: bytes) -> bytes:
    """Decode the UO 'BWT' payload used with UOP compression flag 3.

    The pipeline is:
      zlib(payload) -> bwt/mtf decode -> final bytes
    """

    if buffer is None or len(buffer) < 6:
        raise UopCompressionError("BWT buffer too short")

    # The first 4 bytes are a header (unused by the reference implementation).
    codes = buffer[4:]
    if len(codes) < 2:
        return b""

    # Stage 1: Move-to-front decode. The last code byte acts as a sentinel and
    # does not emit an output byte.
    table = list(range(256))
    mtf = bytearray(len(codes) - 1)
    for i, code in enumerate(codes[:-1]):
        if code >= 256:
            raise UopCompressionError(f"Invalid MTF code: {code}")
        value = table[code]
        if code:
            table.pop(code)
            table.insert(0, value)
        mtf[i] = value

    # Stage 2: Internal UO decoder operating on the MTF output.
    if len(mtf) < 1024:
        raise UopCompressionError("BWT MTF output too short")

    counts = list(struct.unpack_from("<256i", mtf, 0))
    if any(c < 0 for c in counts):
        raise UopCompressionError("Invalid BWT frequency table")

    total = sum(counts)
    out_len = total
    if out_len < 0:
        raise UopCompressionError("Invalid BWT output length")

    # partial[0:256] = counts; partial[256:512] = per-symbol start ptr;
    # partial[512:768] = per-symbol end ptr.
    partial = [0] * (256 * 3)
    partial[0:256] = counts

    non_zero = 0
    for c in counts:
        if c != 0:
            non_zero += 1

    # Order symbols by decreasing frequency.
    tmp = counts[:]
    ordered = []
    for _ in range(256):
        max_val = 0
        max_idx = 0
        for j, v in enumerate(tmp):
            if v > max_val:
                max_val = v
                max_idx = j
        if max_val == 0:
            break
        ordered.append(max_idx)
        tmp[max_idx] = 0

    symbol_table = list(range(256))

    m = 0
    for i in range(non_zero):
        if i >= len(ordered):
            break
        sym = ordered[i] & 0xFF
        pos = 1024 + m
        if pos >= len(mtf):
            raise UopCompressionError("BWT stream truncated")
        symbol_table[mtf[pos]] = sym
        partial[sym + 256] = m + 1
        m += partial[sym]
        partial[sym + 512] = m

    value = symbol_table[0] & 0xFF
    out = bytearray(out_len)

    for i in range(out_len):
        out[i] = value

        start_idx = value + 256
        start = partial[start_idx]
        end = partial[value + 512]

        if start >= end:
            if non_zero > 0:
                non_zero -= 1
                # Remove exhausted symbol from the front of the table.
                for j in range(non_zero):
                    symbol_table[j] = symbol_table[j + 1]
                value = symbol_table[0] & 0xFF
            continue

        pos = 1024 + start
        if pos >= len(mtf):
            raise UopCompressionError("BWT stream truncated")
        idx = mtf[pos]
        partial[start_idx] = start + 1

        if idx != 0:
            if idx >= 256:
                raise UopCompressionError("Invalid BWT index")
            for j in range(idx):
                symbol_table[j] = symbol_table[j + 1]
            symbol_table[idx] = value
            value = symbol_table[0] & 0xFF

    return bytes(out)


class UopFile:
    """A readable UOP container."""

    def __init__(self, path: str | Path, pattern: str, *, has_extra: bool = False):
        self.path = str(path)
        self.pattern = pattern
        self.has_extra = bool(has_extra)
        self._hash_to_entry: Dict[int, UopEntry] = {}
        self._parsed = False

    def parse(self) -> None:
        if self._parsed:
            return

        p = Path(self.path)
        if not p.exists():
            raise FileNotFoundError(self.path)

        with p.open("rb") as f:
            header = f.read(28)
            if len(header) != 28:
                raise UopFormatError("UOP header too short")

            magic, version, ts, next_block, block_size, count = struct.unpack("<IIIqIi", header)
            if magic != _UOP_MAGIC:
                raise UopFormatError("Bad UOP magic")

            if next_block <= 0:
                # Some containers might have no blocks.
                self._parsed = True
                return

            f.seek(next_block)

            while True:
                block_hdr = f.read(12)
                if len(block_hdr) != 12:
                    break

                files_count, next_block = struct.unpack("<Iq", block_hdr)
                for _ in range(int(files_count)):
                    ent = f.read(34)
                    if len(ent) != 34:
                        raise UopFormatError("Unexpected EOF while reading block entries")

                    offset, header_len, comp_len, decomp_len, h, data_hash, flag = struct.unpack(
                        "<qiiiQIh", ent
                    )

                    if offset == 0:
                        continue

                    data_offset = int(offset + header_len)
                    extra1 = 0
                    extra2 = 0

                    if self.has_extra and flag != 3:
                        pos = f.tell()
                        f.seek(data_offset)
                        extra_bytes = f.read(8)
                        if len(extra_bytes) == 8:
                            extra1, extra2 = struct.unpack("<ii", extra_bytes)
                            data_offset += 8
                            comp_len = max(0, comp_len - 8)
                        f.seek(pos)

                    self._hash_to_entry[int(h)] = UopEntry(
                        offset=data_offset,
                        compressed_length=int(comp_len),
                        decompressed_length=int(decomp_len),
                        compression_flag=int(flag),
                        extra1=int(extra1),
                        extra2=int(extra2),
                    )

                if next_block == 0:
                    break

                f.seek(next_block)

        self._parsed = True

    def get_entry(self, entry_id: int) -> Optional[UopEntry]:
        self.parse()
        virtual_name = _format_csharp_pattern(self.pattern, int(entry_id))
        h = create_hash(virtual_name)
        return self._hash_to_entry.get(h)

    def read_raw(self, entry_id: int) -> Optional[bytes]:
        self.parse()
        entry = self.get_entry(int(entry_id))
        if entry is None:
            return None

        if entry.compressed_length <= 0:
            return None

        with open(self.path, "rb") as f:
            f.seek(entry.offset)
            payload = f.read(entry.compressed_length)

        if not payload:
            return None

        try:
            return _decompress(entry.compression_flag, payload, entry.decompressed_length)
        except UopCompressionError:
            # For now, treat unsupported compression as missing.
            raise


class UopBackedIndex:
    """Adapter matching the subset of FileIndex used by loaders (read_raw)."""

    def __init__(
        self,
        uop_path: str | Path,
        pattern: str,
        *,
        has_extra: bool = False,
        file_id: Optional[int] = None,
    ):
        self.file_id = file_id
        self._uop = UopFile(uop_path, pattern, has_extra=has_extra)

    def read_raw(self, index: int) -> Optional[bytes]:
        if index is None or index < 0:
            return None

        if self.file_id is not None:
            try:
                from .verdata import Verdata

                patch = Verdata.read_patch(self.file_id, int(index))
                if patch is not None:
                    return patch
            except Exception:
                pass

        return self._uop.read_raw(int(index))
