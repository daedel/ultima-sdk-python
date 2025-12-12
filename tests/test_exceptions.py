"""Tests for exceptions module."""

import pytest
from ultima_sdk.exceptions import UltimaSDKError, FileParseError, InvalidFileFormatError


class TestUltimaSDKError:
    """Test base exception class."""

    def test_initialization(self) -> None:
        """Test basic initialization."""
        error = UltimaSDKError("Test message")
        assert str(error) == "Test message"
        assert error.message == "Test message"

    def test_with_cause(self) -> None:
        """Test exception with cause."""
        cause = ValueError("Cause")
        error = UltimaSDKError("Test", cause=cause)
        assert error.cause == cause


class TestFileParseError:
    """Test file parsing exception."""

    def test_initialization(self) -> None:
        """Test initialization with file path."""
        error = FileParseError("Invalid data", file_path="test.mul")
        assert "Invalid data" in str(error)
        assert error.file_path == "test.mul"


class TestInvalidFileFormatError:
    """Test invalid file format exception."""

    def test_initialization(self) -> None:
        """Test initialization with expected and actual formats."""
        error = InvalidFileFormatError("MUL", "UOP")
        assert "Expected MUL, got UOP" in str(error)
        assert error.expected == "MUL"
        assert error.actual == "UOP"