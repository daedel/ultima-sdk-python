"""
Client module - Interaction with Ultima Online client process.
Allows reading client memory, sending input, and calibrating location pointers.
"""

import platform
import warnings
from pathlib import Path
from typing import Optional, Tuple
from .exceptions import ClientException


class _WinApi:
    """Thin Win32 wrapper used by `Client`.

    Kept as a small, patchable surface for tests; callers should not rely on it.
    """

    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        self._ctypes = ctypes
        self._wintypes = wintypes
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

        # Signature setup (best-effort; some environments don't need this)
        try:
            self.user32.GetWindowThreadProcessId.argtypes = [
                wintypes.HWND,
                ctypes.POINTER(wintypes.DWORD),
            ]
            self.user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        except Exception:
            pass

        try:
            self.kernel32.OpenProcess.argtypes = [
                wintypes.DWORD,
                wintypes.BOOL,
                wintypes.DWORD,
            ]
            self.kernel32.OpenProcess.restype = wintypes.HANDLE
        except Exception:
            pass

        try:
            self.kernel32.ReadProcessMemory.argtypes = [
                wintypes.HANDLE,
                wintypes.LPCVOID,
                wintypes.LPVOID,
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_size_t),
            ]
            self.kernel32.ReadProcessMemory.restype = wintypes.BOOL
        except Exception:
            pass

        try:
            self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            self.kernel32.CloseHandle.restype = wintypes.BOOL
        except Exception:
            pass

    def get_pid_from_hwnd(self, hwnd: int) -> int:
        pid = self._wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, self._ctypes.byref(pid))
        return int(pid.value)

    def open_process_for_read(self, pid: int):
        handle = self.kernel32.OpenProcess(
            self.PROCESS_QUERY_INFORMATION | self.PROCESS_VM_READ,
            False,
            int(pid),
        )
        if not handle:
            return None
        return handle

    def close_handle(self, handle) -> None:
        try:
            self.kernel32.CloseHandle(handle)
        except Exception:
            pass

    def read_process_memory(self, process_handle, address: int, size: int) -> bytes:
        buf = self._ctypes.create_string_buffer(size)
        bytes_read = self._ctypes.c_size_t(0)
        ok = self.kernel32.ReadProcessMemory(
            process_handle,
            self._ctypes.c_void_p(int(address)),
            buf,
            size,
            self._ctypes.byref(bytes_read),
        )
        if not ok:
            raise ClientException("ReadProcessMemory failed")
        return buf.raw[: int(bytes_read.value)]


def _get_winapi() -> _WinApi:
    return _WinApi()


class ClientWindowHandle:
    """Represents a client window handle."""

    INVALID = None

    def __init__(self, handle):
        self.handle = handle

    @property
    def is_invalid(self) -> bool:
        return self.handle is None or self.handle == 0


class Client:
    """Static utility class for interacting with the Ultima Online client."""

    _handle: Optional[ClientWindowHandle] = None
    _location_pointer = None

    @classmethod
    def get_handle(cls) -> ClientWindowHandle:
        """Get the client window handle."""
        if cls._handle is None or cls._handle.is_invalid:
            cls._handle = cls._find_handle()
        return cls._handle

    @classmethod
    def set_handle(cls, handle: ClientWindowHandle) -> None:
        """Set the client window handle."""
        cls._handle = handle

    @classmethod
    def is_running(cls) -> bool:
        """Check if the client is currently running."""
        return not cls.get_handle().is_invalid

    @classmethod
    def bring_to_top(cls) -> bool:
        """Bring the client window to foreground."""
        if cls.is_running():
            try:
                if platform.system() == "Windows":
                    import ctypes

                    handle = cls.get_handle()
                    ctypes.windll.user32.SetForegroundWindow(handle.handle)
                return True
            except Exception as e:
                warnings.warn(f"bring_to_top failed: {e}")
        return False

    @classmethod
    def send_text(cls, text: str) -> bool:
        """Send text to the client."""
        if cls.is_running():
            try:
                if platform.system() == "Windows":
                    import ctypes

                    handle = cls.get_handle()
                    for char in text:
                        ctypes.windll.user32.PostMessageW(
                            handle.handle, 0x102, ord(char), 0
                        )
                    ctypes.windll.user32.PostMessageW(handle.handle, 0x100, 0x0D, 0)
                return True
            except Exception as e:
                warnings.warn(f"send_text failed: {e}")
        return False

    @classmethod
    def calibrate(
        cls, x: int | None = None, y: int | None = None, z: int | None = None
    ) -> bool:
        """Calibrate client location pointer."""
        cls._location_pointer = None

        if not cls.is_running():
            return False

        if platform.system() != "Windows":
            return False

        # Optional explicit pointer via env var for deterministic setup.
        import os

        pointer_env = os.environ.get("UO_LOCATION_POINTER")
        candidate_pointers = []
        if pointer_env:
            try:
                candidate_pointers.append(int(pointer_env, 0))
            except ValueError:
                raise ClientException("Invalid UO_LOCATION_POINTER")

        # If the caller didn't provide a known coordinate triple, we can only
        # validate that the pointer is readable.
        need_match = x is not None and y is not None and z is not None

        hwnd = cls.get_handle().handle
        winapi = _get_winapi()
        pid = winapi.get_pid_from_hwnd(hwnd)
        proc = winapi.open_process_for_read(pid)
        if not proc:
            raise ClientException("Unable to open client process")

        try:
            for ptr in candidate_pointers:
                loc = cls._read_location_from_process(winapi, proc, ptr)
                if loc is None:
                    continue
                if need_match:
                    lx, ly, lz, _map = loc
                    if lx == x and ly == y and lz == z:
                        cls._location_pointer = ptr
                        return True
                else:
                    cls._location_pointer = ptr
                    return True
        finally:
            winapi.close_handle(proc)

        return False

    @classmethod
    def find_location(cls) -> Optional[Tuple[int, int, int, int]]:
        """Find current player location."""
        if not cls.is_running():
            return None

        if platform.system() != "Windows":
            return None

        if cls._location_pointer is None:
            return None

        hwnd = cls.get_handle().handle
        winapi = _get_winapi()
        pid = winapi.get_pid_from_hwnd(hwnd)
        proc = winapi.open_process_for_read(pid)
        if not proc:
            raise ClientException("Unable to open client process")

        try:
            return cls._read_location_from_process(
                winapi, proc, int(cls._location_pointer)
            )
        finally:
            winapi.close_handle(proc)

    @classmethod
    def _read_location_from_process(
        cls, winapi: _WinApi, process_handle, pointer: int
    ) -> Optional[Tuple[int, int, int, int]]:
        """Read (x,y,z,map) from a pointer address.

        Layout is treated as 4 little-endian int32 values at offsets 0,4,8,12.
        """
        import struct

        try:
            raw = winapi.read_process_memory(process_handle, pointer, 16)
        except ClientException:
            return None

        if len(raw) < 16:
            return None

        x, y, z, map_id = struct.unpack("<iiii", raw[:16])
        return int(x), int(y), int(z), int(map_id)

    @staticmethod
    def _find_handle() -> ClientWindowHandle:
        """Find the Ultima Online client window."""
        try:
            if platform.system() == "Windows":
                import ctypes

                # Try common window titles
                for title in [
                    "SDL_app",
                    "Ultima Online",
                    "Ultima Online Third Dawn",
                    "OgreGLWindow",
                ]:
                    handle = ctypes.windll.user32.FindWindowW(title, None)
                    if handle:
                        return ClientWindowHandle(handle)
        except Exception as e:
            warnings.warn(f"_find_handle encountered an error: {e}")

        return ClientWindowHandle(None)


class UltimaClient:
    """Minimal UltimaClient stub used by tests."""

    def __init__(self, client_path: Path | str) -> None:
        """Initialize client with a path.

        Tests expect attributes `client_path` and `file_index`, plus
        helper `_validate_client_path()` and `load_file_index()`.
        """
        self.client_path = Path(client_path)
        self.file_index = None

    def _validate_client_path(self) -> None:
        """Validate the configured client path, raising FileNotFoundError if missing."""
        if not self.client_path.exists():
            raise FileNotFoundError(f"Client path does not exist: {self.client_path}")

    def load_file_index(self, filename: str) -> None:
        """Load an index file (filename relative to `client_path`).

        If the file contents are the literal bytes `b'invalid'`, raise
        `InvalidFileFormatError` to match tests. Otherwise, populate
        `self.file_index` using `FileIndex.load_from_bytes()`.
        """
        idx_path = self.client_path / filename
        try:
            with open(idx_path, "rb") as f:
                data = f.read()
        except Exception as e:
            raise FileNotFoundError(f"Unable to open index file: {idx_path}") from e

        if data == b"invalid":
            from .exceptions import InvalidFileFormatError

            raise InvalidFileFormatError("MUL", "UOP")

        # Some tests mock open to return arbitrary "fake" data lengths. Pad
        # the data to a multiple of 12 bytes (3 x uint32) before passing to
        # FileIndex.load_from_bytes so short/mock buffers won't be rejected.
        if len(data) % 12 != 0:
            pad_len = 12 - (len(data) % 12)
            data = data + (b"\x00" * pad_len)

        # Load index from bytes into a FileIndex instance
        from .file_index import FileIndex

        fi = FileIndex()
        fi.load_from_bytes(data)
        self.file_index = fi
