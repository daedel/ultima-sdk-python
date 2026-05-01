# Contributing to Ultima SDK Python

Thanks for your interest in contributing! Here's how to get started.

## Setting Up Your Environment

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/ultima-sdk-python.git
cd ultima-sdk-python
```

### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or for bugs:
git checkout -b fix/your-bug-fix
```

### 3. Install Dependencies
```bash
pip install -e .
pip install pytest pytest-cov black ruff mypy pre-commit
pre-commit install  # Install hooks for automatic linting
```

## Code Standards

We follow strict code quality standards:

### Formatting
- **Black** (100-char line length): `black ultima_sdk tests`
- **Ruff** linting: `ruff check ultima_sdk tests --fix`
- **mypy** type checking: `mypy ultima_sdk --ignore-missing-imports`

### Tests
All code must include tests:
```bash
pytest tests/ -v  # Run all tests
pytest tests/test_art.py -v  # Run specific test file
```

Check coverage:
```bash
pytest tests/ --cov=ultima_sdk --cov-report=term
```

Aim for **>80% coverage** on new code.

## Pull Request Workflow

1. **Create a descriptive commit** with clear messages
   ```
   feat: Add support for Texture decoding
   fix: Correct RLE decode offset calculation
   docs: Update module docstrings
   refactor: Simplify FileIndex interface
   ```

2. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a PR** on GitHub with:
   - Clear description of changes
   - Link to related issues
   - Evidence of test coverage

4. **Address review feedback** and re-request review

## Pre-Commit Hooks

On `git commit`, the following automatically run:
- Black formatter
- Ruff linter (with auto-fix)
- Trailing whitespace removal
- Merge conflict detection
- mypy type checking

If hooks fail, fix the issues and retry commit.

## Module Status

### Fully Implemented ✅
- `art.py` — Static art decoding (RLE + raw pixels)
- `tiledata.py` — Land/item properties
- `hues.py` — Color palettes
- `animations.py` — Animation frames
- `equipconv.py` — Paperdoll mapping
- `rendering.py` — Pixel→PIL.Image conversion

### WIP / Stubs ⚠️
- `sound.py`, `map.py`, `textures.py`, `light.py`, `multis.py` — Paths exist, decoding incomplete

Contributions to stub modules are especially welcome!

## Questions?

Open an [issue](https://github.com/UltimaWorks/ultima-sdk-python/issues) or start a [discussion](https://github.com/UltimaWorks/ultima-sdk-python/discussions).

Thanks for contributing! 🎮
