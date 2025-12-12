# GitHub Copilot Instructions

## Project Summary

This repository contains **ultima-sdk-python**, a Python library for extracting client information and rendering images from Ultima Online client files. The SDK provides tools to interact with, parse, and manipulate data from the classic MMORPG Ultima Online Client Files.

## Structure Overview

This is a Python SDK project organized as follows:

- `/` - Root directory containing README and configuration files
- `README.md` - Main project documentation
- Future structure will include:
  - `/ultima/` or `/src/` - Main source code for the SDK
  - `/tests/` - Test files using pytest or unittest
  - `/docs/` - Additional documentation
  - `/examples/` - Example usage scripts

## Contribution Guidelines

### Development Setup

1. **Python Version**: Use Python 3.8 or higher
2. **Virtual Environment**: Always work within a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Dependencies**: Install using pip
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

### Code Quality

- **Formatting**: Use `black` for code formatting
  ```bash
  black .
  ```
- **Linting**: Use `ruff` for linting (preferred for modern Python projects)
  ```bash
  ruff check .
  ```
- **Type Hints**: Use type hints for all functions and methods
- **Docstrings**: Use Google-style docstrings for all public APIs

### Testing

- **Framework**: Use `pytest` for all tests
- **Coverage**: Maintain high test coverage (aim for 80%+)
- **Running Tests**:
  ```bash
  pytest
  pytest --cov=ultima  # With coverage
  ```
- **Test Files**: Place tests in `/tests/` directory, mirroring the source structure
- **Test Naming**: Use descriptive names starting with `test_`

### Commit Guidelines

- Write clear, descriptive commit messages
- Use conventional commit format when applicable:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation changes
  - `test:` for test additions/modifications
  - `refactor:` for code refactoring
  - `chore:` for maintenance tasks

## Key Principles

### Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Keep functions focused and small (single responsibility principle)
- Avoid deep nesting (max 3-4 levels)

### Architecture

- **Modularity**: Keep components loosely coupled
- **Error Handling**: Use proper exception handling with custom exceptions when needed
- **Performance**: Consider performance for file parsing operations
- **Compatibility**: Maintain compatibility with major Ultima Online client versions

### Documentation

- Every public class, method, and function must have a docstring
- Include type hints for better IDE support and type checking
- Document expected file formats and data structures
- Provide usage examples in docstrings for complex APIs

### Security

- Validate all input data, especially when parsing binary files
- Handle file I/O errors gracefully
- Be cautious with file paths and prevent directory traversal attacks
- Don't commit sensitive data or credentials

## Additional Documentation

As the project grows, refer to:

- `README.md` - Getting started guide and overview
- `CONTRIBUTING.md` - Detailed contribution guidelines (when created)
- `/docs/` - API documentation and guides (when created)
- GitHub Issues - For feature requests and bug tracking
- GitHub Discussions - For questions and community interaction

## Technologies and Tools

- **Language**: Python 3.8+
- **Suggested Third-Party Libraries**:
  - `pillow` - For image rendering
  - `numpy` - For efficient data manipulation
  - `pytest` - For testing
  - `black` - For code formatting
  - `ruff` - For linting
  - `mypy` - For type checking
- **Standard Library Modules**:
  - `struct` - For binary file parsing
  - `pathlib` - For file path handling
  - `typing` - For type hints

## Getting Started for Contributors

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature/fix
4. Make your changes following the guidelines above
5. Run tests and ensure they pass
6. Format your code with black
7. Commit your changes
8. Push to your fork
9. Create a pull request

## Notes for Copilot

- This project is in early stages of development
- Focus on creating clean, well-documented, and tested code
- When adding new features, consider backwards compatibility
- Binary file parsing requires careful attention to byte order and data structures
- Image rendering should support various Ultima Online file formats (e.g., .mul, .uop)
