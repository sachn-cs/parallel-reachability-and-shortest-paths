# Deployment

This document covers how to deploy and distribute reachq.

## Installation Methods

### For Users

```bash
# Install from PyPI (when published)
pip install reachq

# Install from source
git clone https://github.com/sachncs/parallel-reachability-and-shortest-paths.git
cd parallel-reachability-and-shortest-paths
pip install .
```

### For Developers

```bash
# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

## Building Packages

### Source Distribution

```bash
pip install build
python -m build --sdist
```

### Wheel Distribution

```bash
pip install build
python -m build --wheel
```

### Verify Package

```bash
pip install twine
twine check dist/*
```

## Publishing to PyPI

### Prerequisites

- PyPI account
- API token (recommended over password)

### Steps

1. Build the package:
   ```bash
   python -m build
   ```

2. Upload to TestPyPI first (recommended):
   ```bash
   twine upload --repository testpypi dist/*
   ```

3. Test the installation:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ reachq
   ```

4. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

### Automated Publishing (Recommended)

Set up GitHub Actions for automated publishing on release:

```yaml
# .github/workflows/release.yml
name: Release

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

## Environment Configuration

reachq does not require environment variables for basic usage. See
`.env.example` for optional configuration.

## Docker (Optional)

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install .

CMD ["python", "scripts/demo.py"]
```

### Build and Run

```bash
docker build -t reachq .
docker run reachq
```

## Performance Considerations

### Dependencies

- **numpy**: Uses BLAS for matrix operations. For optimal performance, install
  a optimized BLAS library (OpenBLAS, MKL, or Accelerate on macOS).

### Memory

- Large graphs may require significant memory. Monitor usage when processing
  graphs with millions of vertices.

### CPU

- Current implementation is single-threaded Python. For large-scale processing,
  consider parallelizing at the application level.

## Monitoring

### Logging

The library uses Python's built-in `logging` module. Enable debug output:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Profiling

Built-in profiling support via `reachq.work_depth`:

```python
from reachq.work_depth import WorkDepthAccountant

wd = WorkDepthAccountant()
wd.start_timer()
# ... run algorithm ...
wd.stop_timer()
print(wd.summary())
```
