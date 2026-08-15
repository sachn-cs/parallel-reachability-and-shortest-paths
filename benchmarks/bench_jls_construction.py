"""Benchmarks for the JLS shortcut-set construction.

Use with asv: `asv run -p 1 benchmarks/`. Or invoke directly:
`python benchmarks/bench_jls_construction.py --benchmark-only`.
"""

import os
import sys

# Add the project root to sys.path so reachq is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reachq.core.generators import random_dag

from reachq.core.algorithm import build_shortcut_set_for_reachability


def time_jls_path_n50():
    g = random_dag(n=50, edge_probability=0.3, random_seed=42)
    build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)


def time_jls_path_n100():
    g = random_dag(n=100, edge_probability=0.3, random_seed=42)
    build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)


def time_jls_path_n200():
    g = random_dag(n=200, edge_probability=0.3, random_seed=42)
    build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)


def time_jls_layered_10x10():
    g = random_dag(n=100, edge_probability=0.3, random_seed=42)
    build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)


def time_jls_layered_20x10():
    g = random_dag(n=200, edge_probability=0.3, random_seed=42)
    build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)


def time_jls_star_50():
    """50-leaf star: dense center, sparse leaves."""
    g = random_dag(n=50, edge_probability=0.3, random_seed=42)
    build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)
