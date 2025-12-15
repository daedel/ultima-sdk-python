"""Tests for art module."""

import pytest
from io import BytesIO
from PIL import Image
from ultima_sdk.art import ArtLoader, ArtTile
from ultima_sdk.exceptions import FileParseError


class TestArtTile:
    """Test ArtTile class."""

    def test_initialization(self) -> None:
        """Test tile creation."""
        tile = ArtTile(width=44, height=44, data=b"fake pixels")
        assert tile.width == 44
        assert tile.height == 44
        assert tile.data == b"fake pixels"

    def test_to_image(self) -> None:
        """Test converting to PIL Image."""
        # Mock RGBA data
        data = b'\xFF\x00\x00\xFF' * (44 * 44)  # Red pixels
        tile = ArtTile(44, 44, data)
        img = tile.to_image()
        assert isinstance(img, Image.Image)
        assert img.size == (44, 44)


class TestArtLoader:
    """Test ArtLoader class."""

    @pytest.fixture
    def loader(self) -> ArtLoader:
        """Create a test loader."""
        return ArtLoader("dummy_path")

    @pytest.fixture
    def sample_art_data(self) -> bytes:
        """Sample art.mul data (mocked header + tile)."""
        # Mock: width=44, height=44, then pixel data
        header = b'\x2C\x00\x2C\x00'  # Little-endian uint16
        pixels = b'\x00' * (44 * 44 * 2)  # Mock 16-bit pixels
        return header + pixels

    def test_load_tile(self, loader: ArtLoader, sample_art_data: bytes) -> None:
        """Test loading a tile via FileIndex + file read."""
        with patch.object(loader, 'file_index') as mock_index:
            mock_index.get_entry.return_value = type(
                'Entry', (), {'offset': 0, 'length': len(sample_art_data)}
            )()
            with patch('builtins.open', mock_open(read_data=sample_art_data)):
                tile = loader.load_tile(0)
                assert tile is not None
                assert tile.width == 44
                assert tile.height == 44

    def test_load_tile_invalid_data(self, loader: ArtLoader) -> None:
        """Test loading invalid data raises FileParseError."""
        with patch.object(loader, 'file_index') as mock_index:
            mock_index.get_entry.return_value = type(
                'Entry', (), {'offset': 0, 'length': 7}
            )()
            with patch('builtins.open', mock_open(read_data=b"invalid")):
                with pytest.raises(FileParseError):
                    loader.load_tile(0)

    @pytest.mark.parametrize("tile_id", [0, 1000, 0x3FFF])  # Valid range
    def test_load_tile_by_id(self, loader: ArtLoader, sample_art_data: bytes, tile_id: int) -> None:
        """Test loading tile by ID."""
        # Assuming loader has a method to load by ID with index
        with patch.object(loader, 'file_index') as mock_index:
            mock_index.get_entry.return_value = type('Entry', (), {'offset': 0, 'length': len(sample_art_data)})()
            with patch("builtins.open", mock_open(read_data=sample_art_data)):
                tile = loader.load_tile_by_id(tile_id)
                assert isinstance(tile, ArtTile)