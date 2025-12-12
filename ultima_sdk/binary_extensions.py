"""
Binary I/O extension utilities for reading/writing Ultima data files.
"""

import struct
from typing import BinaryIO, Union, List, Tuple
from io import BytesIO


class BinaryReader:
    """Helper class for reading binary data."""

    def __init__(self, data: Union[bytes, BinaryIO]):
        if isinstance(data, bytes):
            self.stream = BytesIO(data)
        else:
            self.stream = data

    def read(self, count: int) -> bytes:
        """Read count bytes."""
        return self.stream.read(count)

    def read_byte(self) -> int:
        """Read single byte."""
        return struct.unpack('B', self.stream.read(1))[0]

    def read_sbyte(self) -> int:
        """Read signed byte."""
        return struct.unpack('b', self.stream.read(1))[0]

    def read_int16(self) -> int:
        """Read 16-bit signed integer (little-endian)."""
        return struct.unpack('<h', self.stream.read(2))[0]

    def read_uint16(self) -> int:
        """Read 16-bit unsigned integer (little-endian)."""
        return struct.unpack('<H', self.stream.read(2))[0]

    def read_int32(self) -> int:
        """Read 32-bit signed integer (little-endian)."""
        return struct.unpack('<i', self.stream.read(4))[0]

    def read_uint32(self) -> int:
        """Read 32-bit unsigned integer (little-endian)."""
        return struct.unpack('<I', self.stream.read(4))[0]

    def read_int64(self) -> int:
        """Read 64-bit signed integer (little-endian)."""
        return struct.unpack('<q', self.stream.read(8))[0]

    def read_uint64(self) -> int:
        """Read 64-bit unsigned integer (little-endian)."""
        return struct.unpack('<Q', self.stream.read(8))[0]

    def read_float(self) -> float:
        """Read 32-bit float (little-endian)."""
        return struct.unpack('<f', self.stream.read(4))[0]

    def read_double(self) -> float:
        """Read 64-bit double (little-endian)."""
        return struct.unpack('<d', self.stream.read(8))[0]

    def read_string(self, length: int = None, encoding: str = 'utf-8', null_terminated: bool = False) -> str:
        """Read string with optional null-termination."""
        if length is not None:
            data = self.stream.read(length)
        elif null_terminated:
            data = b''
            while True:
                byte = self.stream.read(1)
                if not byte or byte == b'\x00':
                    break
                data += byte
        else:
            raise ValueError("Either length or null_terminated must be specified")

        return data.decode(encoding, errors='replace').rstrip('\x00')

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek to offset."""
        return self.stream.seek(offset, whence)

    def tell(self) -> int:
        """Get current position."""
        return self.stream.tell()

    def close(self) -> None:
        """Close the stream."""
        if hasattr(self.stream, 'close'):
            self.stream.close()


class BinaryWriter:
    """Helper class for writing binary data."""

    def __init__(self, stream: BinaryIO = None):
        self.stream = stream or BytesIO()

    def write(self, data: bytes) -> None:
        """Write bytes."""
        self.stream.write(data)

    def write_byte(self, value: int) -> None:
        """Write unsigned byte."""
        self.stream.write(struct.pack('B', value))

    def write_sbyte(self, value: int) -> None:
        """Write signed byte."""
        self.stream.write(struct.pack('b', value))

    def write_int16(self, value: int) -> None:
        """Write 16-bit signed integer (little-endian)."""
        self.stream.write(struct.pack('<h', value))

    def write_uint16(self, value: int) -> None:
        """Write 16-bit unsigned integer (little-endian)."""
        self.stream.write(struct.pack('<H', value))

    def write_int32(self, value: int) -> None:
        """Write 32-bit signed integer (little-endian)."""
        self.stream.write(struct.pack('<i', value))

    def write_uint32(self, value: int) -> None:
        """Write 32-bit unsigned integer (little-endian)."""
        self.stream.write(struct.pack('<I', value))

    def write_int64(self, value: int) -> None:
        """Write 64-bit signed integer (little-endian)."""
        self.stream.write(struct.pack('<q', value))

    def write_uint64(self, value: int) -> None:
        """Write 64-bit unsigned integer (little-endian)."""
        self.stream.write(struct.pack('<Q', value))

    def write_float(self, value: float) -> None:
        """Write 32-bit float (little-endian)."""
        self.stream.write(struct.pack('<f', value))

    def write_double(self, value: float) -> None:
        """Write 64-bit double (little-endian)."""
        self.stream.write(struct.pack('<d', value))

    def write_string(self, value: str, encoding: str = 'utf-8', null_terminated: bool = False) -> None:
        """Write string."""
        data = value.encode(encoding)
        self.stream.write(data)
        if null_terminated:
            self.stream.write(b'\x00')

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek to offset."""
        return self.stream.seek(offset, whence)

    def tell(self) -> int:
        """Get current position."""
        return self.stream.tell()

    def get_buffer(self) -> bytes:
        """Get accumulated bytes."""
        if isinstance(self.stream, BytesIO):
            return self.stream.getvalue()
        return None

    def close(self) -> None:
        """Close the stream."""
        if hasattr(self.stream, 'close'):
            self.stream.close()
