"""Benchmarks for the iterative refinement of shortcut sets.

Same pattern as benchmarks/bench_sparsify.py but focused on
iterative_shortcut_set. Shows the convergence of |H| across iterations.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reachq.generators import random_dag
from reachq.research.iterate import iterative_shortcut_set


def time_iterate_1_iter_n100():
    g = random_dag(n=100, edge_probability=0.3, random_seed=42)
    iterative_shortcut_set(g, omega=3.0, max_iterations=1, random_seed=42)


def time_iterate_3_iter_n100():
    g = random_dag(n=100, edge_probability=0.3, random_seed=42)
    iterative_shortcut_set(g, omega=3.0, max_iterations=3, random_seed=42)


def time_iterate_5_iter_n100():
    g = random_dag(n=100, edge_probability=0.3, random_seed=42)
    iterative_shortcut_set(g, omega=3.0, max_iterations=5, random_seed=42)
