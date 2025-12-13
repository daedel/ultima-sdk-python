"""Tests for client module."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from ultima_sdk.client import UltimaClient
from ultima_sdk.exceptions import InvalidFileFormatError


class TestUltimaClient:
    """Test UltimaClient class."""

    @pytest.fixture
    def client(self) -> UltimaClient:
        """Create a test client instance."""
        return UltimaClient(client_path=Path("/fake/path"))

    def test_initialization(self, client: UltimaClient) -> None:
        """Test client initialization."""
        assert client.client_path == Path("/fake/path")
        assert client.file_index is None

    @patch("ultima_sdk.client.Path.exists")
    def test_validate_client_path_exists(self, mock_exists: patch, client: UltimaClient) -> None:
        """Test path validation when exists."""
        mock_exists.return_value = True
        client._validate_client_path()  # Assuming private method
        # No exception raised

    @patch("ultima_sdk.client.Path.exists")
    def test_validate_client_path_not_exists(self, mock_exists: patch, client: UltimaClient) -> None:
        """Test path validation when not exists."""
        mock_exists.return_value = False
        with pytest.raises(FileNotFoundError):
            client._validate_client_path()

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake data")
    def test_load_file_index(self, mock_file: mock_open, client: UltimaClient) -> None:
        """Test loading file index."""
        client.load_file_index("artidx.mul")
        # Assuming load_file_index sets self.file_index
        assert client.file_index is not None

    def test_load_file_index_invalid_format(self, client: UltimaClient) -> None:
        """Test loading invalid format raises error."""
        with patch("builtins.open", mock_open(read_data=b"invalid")):
            with pytest.raises(InvalidFileFormatError):
                client.load_file_index("invalid.mul")