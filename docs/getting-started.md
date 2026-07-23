# Getting Started

This guide walks you through setting up and using PRSPNSD for the first time.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/sachncs/parallel-reachability-and-shortest-paths.git
cd parallel-reachability-and-shortest-paths

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Run the test suite
pytest

# Run the demo
python scripts/demo.py
```

## Quick Start

### 1. Build a Graph

```python
from reachq.graph import Digraph

g = Digraph()
for i in range(100):
    g.add_vertex(i)
for i in range(99):
    g.add_edge(i, i + 1)
```

### 2. Construct a Shortcut Set

```python
from reachq.shortcut_set import build_shortcut_set_for_reachability

shortcuts, beta = build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
print(f"Constructed {len(shortcuts)} shortcut edges (beta={beta:.2f})")
```

### 3. Query Reachability

```python
from reachq.reachability import parallel_bfs, bfs_reachability

source = 0
reachable = parallel_bfs(g, source, shortcuts)

# Verify correctness
assert reachable == bfs_reachability(g, source)
print(f"Vertex {source} can reach {len(reachable)} vertices")
```

## Next Steps

- Read the [Architecture](architecture.md) guide to understand the codebase structure
- Explore the [API Reference](index.md) for complete function documentation
- Check out the [Algorithms](algorithms.md) documentation for theoretical background
- Review the [Benchmarks](benchmarks.md) guide for performance evaluation

## Troubleshooting

### Common Issues

**ImportError: No module named 'reachq'**

Ensure you've installed the package in editable mode:
```bash
pip install -e ".[dev]"
```

**numpy not found**

numpy is a required dependency. Install it with:
```bash
pip install numpy>=1.21.0
```

**Tests failing**

Make sure you're using Python 3.9+ and have all dev dependencies installed:
```bash
pip install -e ".[dev]"
pytest
```

For more help, see the [FAQ](faq.md) or open an [issue](https://github.com/sachncs/parallel-reachability-and-shortest-paths/issues).
