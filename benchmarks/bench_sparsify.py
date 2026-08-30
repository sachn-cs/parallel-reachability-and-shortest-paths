"""Benchmarks for the post-processing refinements (sparsify, iterate).

Compare JLS-only, JLS+sparsify (reach-only),
JLS+sparsify_hop_bounded, and JLS+iterate. All on the same input
graph.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reachq.generators import random_dag
from reachq.shortcut import build_shortcut_set_for_reachability
from reachq.research.iterate import iterative_shortcut_set
from reachq.research.sparsify import sparsify_shortcut_set
from reachq.research.sparsify_hop import sparsify_hop_bounded


def time_jls_only_n100():
    g = random_dag(n=100, edge_probability=0.3, random_seed=42)
    build_shortcut_set_for_reachability(g, omega=3.0, random_seed=42)


def time_jls_sparsify_n100():
    g = random_dag(n=100, edge_probability=0.3, random_seed=42)
    H, _, _ = build_shortcut_set_for_reachability(
        g, omega=3.0, random_seed=42
    )
    sparsify_shortcut_set(g, H)


def time_jls_hop_bounded_n100():
    g = random_dag(n=100, edge_probability=0.3, random_seed=42)
    H, _, _ = build_shortcut_set_for_reachability(
        g, omega=3.0, random_seed=42
    )
    sparsify_hop_bounded(g, H, beta=4)


def time_jls_iterate_n100():
    g = random_dag(n=100, edge_probability=0.3, random_seed=42)
    iterative_shortcut_set(g, omega=3.0, max_iterations=3, random_seed=42)
