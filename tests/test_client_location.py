"""Tests for Client memory location helpers.

These tests are fully mocked; they do not require a running UO client.
"""

import os
import struct
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ultima_sdk.client import Client, ClientWindowHandle
from ultima_sdk.exceptions import ClientException


class FakeWinApi:
    def __init__(self, *, pid: int = 1337, memory: dict[int, bytes] | None = None, open_ok: bool = True):
        self._pid = pid
        self._memory = memory or {}
        self._open_ok = open_ok
        self.closed = False

    def get_pid_from_hwnd(self, hwnd: int) -> int:
        return self._pid

    def open_process_for_read(self, pid: int):
        if not self._open_ok:
            return None
        return SimpleNamespace(pid=pid)

    def close_handle(self, handle) -> None:
        self.closed = True

    def read_process_memory(self, process_handle, address: int, size: int) -> bytes:
        data = self._memory.get(int(address), b"")
        return data[:size]


@pytest.fixture(autouse=True)
def _reset_client_state():
    Client.set_handle(ClientWindowHandle(None))
    Client._location_pointer = None
    yield
    Client.set_handle(ClientWindowHandle(None))
    Client._location_pointer = None


def test_find_location_not_running_returns_none():
    with patch("ultima_sdk.client.platform.system", return_value="Windows"):
        Client.set_handle(ClientWindowHandle(None))
        assert Client.find_location() is None


def test_find_location_not_calibrated_returns_none():
    with patch("ultima_sdk.client.platform.system", return_value="Windows"):
        Client.set_handle(ClientWindowHandle(123))
        assert Client.find_location() is None


def test_find_location_reads_from_pointer():
    ptr = 0x1000
    payload = struct.pack("<iiii", 10, 20, -5, 1)
    fake = FakeWinApi(memory={ptr: payload})

    with patch("ultima_sdk.client.platform.system", return_value="Windows"), \
         patch("ultima_sdk.client._get_winapi", return_value=fake):
        Client.set_handle(ClientWindowHandle(123))
        Client._location_pointer = ptr
        assert Client.find_location() == (10, 20, -5, 1)
        assert fake.closed is True


def test_calibrate_uses_env_pointer_and_matches_xyz(monkeypatch):
    ptr = 0x2000
    payload = struct.pack("<iiii", 150, 250, 0, 0)
    fake = FakeWinApi(memory={ptr: payload})

    monkeypatch.setenv("UO_LOCATION_POINTER", hex(ptr))

    with patch("ultima_sdk.client.platform.system", return_value="Windows"), \
         patch("ultima_sdk.client._get_winapi", return_value=fake):
        Client.set_handle(ClientWindowHandle(123))
        ok = Client.calibrate(x=150, y=250, z=0)
        assert ok is True
        assert Client._location_pointer == ptr


def test_calibrate_invalid_env_pointer_raises(monkeypatch):
    monkeypatch.setenv("UO_LOCATION_POINTER", "not-a-number")

    with patch("ultima_sdk.client.platform.system", return_value="Windows"), \
         patch("ultima_sdk.client._get_winapi", return_value=FakeWinApi()):
        Client.set_handle(ClientWindowHandle(123))
        with pytest.raises(ClientException):
            Client.calibrate(x=1, y=2, z=3)


def test_calibrate_open_process_failure_raises(monkeypatch):
    ptr = 0x3000
    monkeypatch.setenv("UO_LOCATION_POINTER", hex(ptr))

    with patch("ultima_sdk.client.platform.system", return_value="Windows"), \
         patch("ultima_sdk.client._get_winapi", return_value=FakeWinApi(open_ok=False)):
        Client.set_handle(ClientWindowHandle(123))
        with pytest.raises(ClientException):
            Client.calibrate(x=1, y=2, z=3)


def test_calibrate_no_env_pointer_returns_false(monkeypatch):
    monkeypatch.delenv("UO_LOCATION_POINTER", raising=False)

    with patch("ultima_sdk.client.platform.system", return_value="Windows"), \
         patch("ultima_sdk.client._get_winapi", return_value=FakeWinApi()):
        Client.set_handle(ClientWindowHandle(123))
        assert Client.calibrate(x=1, y=2, z=3) is False
