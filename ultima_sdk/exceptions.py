"""
Custom exceptions for the Ultima SDK.
"""


class UltimaSdkException(Exception):
    """Base exception for all Ultima SDK errors.

    Accepts an optional `cause` keyword argument to chain underlying exceptions.
    """

    def __init__(self, message: str = "", *, cause: Exception | None = None, **kwargs) -> None:
        super().__init__(message)
        self.cause = cause


class FileAccessException(UltimaSdkException):
    """Raised when a file cannot be accessed or read."""

    def __init__(self, message: str = "", *, file_path: str | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.file_path = file_path


class InvalidFormatException(UltimaSdkException):
    """Raised when file format is invalid or corrupted."""

    def __init__(self, expected: str, actual: str, **kwargs) -> None:
        msg = f"Expected {expected}, got {actual}"
        super().__init__(msg, **kwargs)
        self.expected = expected
        self.actual = actual


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
