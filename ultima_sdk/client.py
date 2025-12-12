"""
Client module - Interaction with Ultima Online client process.
Allows reading client memory, sending input, and calibrating location pointers.
"""

import platform
from pathlib import Path
from typing import Optional, Tuple
from .exceptions import ClientException


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
                    ctypes.windll.user32.SetForegroundWindow(cls._handle.handle)
                return True
            except Exception:
                pass
        return False

    @classmethod
    def send_text(cls, text: str) -> bool:
        """Send text to the client."""
        if cls.is_running():
            try:
                if platform.system() == "Windows":
                    import ctypes
                    for char in text:
                        ctypes.windll.user32.PostMessageW(cls._handle.handle, 0x102, ord(char), 0)
                    ctypes.windll.user32.PostMessageW(cls._handle.handle, 0x100, 0x0D, 0)
                return True
            except Exception:
                pass
        return False

    @classmethod
    def calibrate(cls, x: int = None, y: int = None, z: int = None) -> bool:
        """Calibrate client location pointer."""
        cls._location_pointer = None
        # Implementation would require memory access
        return False

    @classmethod
    def find_location(cls) -> Optional[Tuple[int, int, int, int]]:
        """Find current player location."""
        # Implementation would require memory access
        return None

    @staticmethod
    def _find_handle() -> ClientWindowHandle:
        """Find the Ultima Online client window."""
        try:
            if platform.system() == "Windows":
                import ctypes
                # Try common window titles
                for title in ["SDL_app", "Ultima Online", "Ultima Online Third Dawn", "OgreGLWindow"]:
                    handle = ctypes.windll.user32.FindWindowW(title, None)
                    if handle:
                        return ClientWindowHandle(handle)
        except Exception:
            pass

        return ClientWindowHandle(None)


class UltimaClient:
    """Minimal UltimaClient stub used by tests."""

    def __init__(self, client_path: Path | str) -> None:
        """Initialize client with a path (no real client ops performed)."""
        self.path = Path(client_path)
        self.attached: bool = False

    def attach(self) -> None:
        """Stub attach method."""
        self.attached = True

    def detach(self) -> None:
        """Stub detach method."""
        self.attached = False

    def is_attached(self) -> bool:
        return self.attached
