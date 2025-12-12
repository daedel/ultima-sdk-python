"""
Custom exceptions for the Ultima SDK.
"""


class UltimaSdkException(Exception):
    """Base exception for all Ultima SDK errors."""
    pass


class FileAccessException(UltimaSdkException):
    """Raised when a file cannot be accessed or read."""
    pass


class InvalidFormatException(UltimaSdkException):
    """Raised when file format is invalid or corrupted."""
    pass


class ClientException(UltimaSdkException):
    """Raised when client window operations fail."""
    pass


class CalibrationException(UltimaSdkException):
    """Raised when client calibration fails."""
    pass


class WaveFormatException(UltimaSdkException):
    """Raised when WAV format is invalid."""
    pass


# Compatibility aliases / legacy names expected by tests
class UltimaSDKError(UltimaSdkException):
    """Backward-compatible alias for older code/tests."""
    pass


class FileParseError(FileAccessException):
    """Backward-compatible alias for file parse/access errors."""
    pass


class InvalidFileFormatError(InvalidFormatException):
    """Backward-compatible alias for invalid file format errors."""
    pass
