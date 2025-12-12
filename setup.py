
"""
Setup configuration for the Ultima SDK Python package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ultima-sdk-python",
    version="1.0.0",
    author="UltimaWorks",
    description="A 1:1 Python conversion of the C# Ultima SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/UltimaWorks/ultima-sdk-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    keywords="ultima online sdk client muls",
)
