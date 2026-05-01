"""Minimal setup.py shim for PEP 517 compatibility.

All configuration is defined in pyproject.toml.
This file exists only for backward compatibility with older tools.
"""

from setuptools import setup

if __name__ == "__main__":
    setup()
