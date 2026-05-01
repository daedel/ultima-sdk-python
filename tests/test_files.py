import os
import pytest
from ultima_sdk.files import Files
from ultima_sdk.exceptions import FileAccessException


def test_require_file_path_raises_when_missing():
    # Ensure no paths are loaded
    Files._mul_path = {}
    with pytest.raises(FileAccessException):
        Files.require_file_path("nonexistent.mul")


def test_require_file_path_success(tmp_path):
    d = tmp_path
    f = d / "art.mul"
    f.write_text("dummy")
    Files.set_directory(str(d))
    path = Files.require_file_path("art.mul")
    assert os.path.exists(path)
    assert os.path.basename(path) == "art.mul"


def test_require_files_multiple(tmp_path):
    d = tmp_path
    f1 = d / "a.mul"
    f2 = d / "b.mul"
    f1.write_text("x")
    f2.write_text("y")
    Files.set_directory(str(d))
    res = Files.require_files(["a.mul", "b.mul"])
    assert "a.mul" in res and "b.mul" in res
    assert os.path.exists(res["a.mul"]) and os.path.exists(res["b.mul"])


def test_require_files_raises_for_missing(tmp_path):
    d = tmp_path
    f1 = d / "a.mul"
    f1.write_text("x")
    Files.set_directory(str(d))
    with pytest.raises(FileAccessException):
        Files.require_files(["a.mul", "missing.mul"])
