# Publishing ZON to PyPI

This guide details the steps to release a new version of `zon-format` to PyPI.

## Prerequisites

1.  **PyPI Account**: You need an account on [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/).
2.  **API Token**: Generate an API token on PyPI and configure it in your `~/.pypirc` or use it directly.
3.  **Build Tools**: Ensure `build` and `twine` are installed:
    ```bash
    pip install build twine
    ```

## 1. Prepare Release

1.  **Update Version**:
    - Edit `pyproject.toml`: `version = "1.0.1"`
    - Edit `src/zon/constants.py`: `VERSION = 8.0` (Format version, not package version)
    - Update `CHANGELOG.md` with release notes.

2.  **Verify**:
    - Run tests: `python -m pytest tests/`
    - Run benchmarks: `python benchmarks/run.py`
    - Check documentation: `README.md`, `EXAMPLES.md`

## 2. Build Package

Clean previous builds and create new distribution files:

```bash
rm -rf dist/
python -m build
```

This will create `dist/zon_format-1.0.1-py3-none-any.whl` and `dist/zon_format-1.0.1.tar.gz`.

## 3. Test Release (TestPyPI)

Upload to TestPyPI first to verify everything looks correct:

```bash
python -m twine upload --repository testpypi dist/*
```

Install from TestPyPI to verify:

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps zon-format
```

## 4. Official Release (PyPI)

Once verified, upload to the official PyPI repository:

```bash
python -m twine upload dist/*
```

## 5. Post-Release

1.  **Tag Release**:
    ```bash
    git tag v1.0.1
    git push origin v1.0.1
    ```
2.  **GitHub Release**: Create a new release on GitHub with the changelog.

---

**Troubleshooting**:
- If upload fails with "File already exists", ensure you bumped the version number.
- If installation fails, check `MANIFEST.in` to ensure all files are included.
