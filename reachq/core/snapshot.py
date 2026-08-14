"""Graph snapshot for algorithm diagnostics.

Captures a point-in-time summary of a graph's structural properties.
Useful for logging, debugging, and comparing inputs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Point-in-time summary of a graph's structural properties."""

    n: int
    """Number of vertices."""
    m: int
    """Number of edges."""
    max_in_degree: int
    """Maximum in-degree across all vertices."""
    max_out_degree: int
    """Maximum out-degree across all vertices."""
    num_sccs: int
    """Number of strongly connected components."""
    rho: float
    """Density ratio: m / n^2."""
    density: float
    """Edge density: m / (n * (n - 1)) for directed graphs."""

    @classmethod
    def from_graph(cls, graph: object) -> Snapshot:
        """Build a snapshot from a Digraph (or any object with the right attrs)."""
        from reachq.core.graph import Digraph

        if not isinstance(graph, Digraph):
            raise TypeError(f"Expected Digraph, got {type(graph).__name__}")
        n = graph.num_vertices()
        m = graph.num_edges()
        max_in = max(
            (len(graph.in_edges.get(v, set())) for v in graph.vertices()), default=0
        )
        max_out = max(
            (len(graph.out_edges.get(v, set())) for v in graph.vertices()), default=0
        )
        from reachq.core.reachability import strongly_connected_components

        sccs = strongly_connected_components(graph)
        num_sccs = len(sccs)
        rho = m / (n * n) if n > 0 else 0.0
        density = m / (n * (n - 1)) if n > 1 else 0.0
        return cls(
            n=n,
            m=m,
            max_in_degree=max_in,
            max_out_degree=max_out,
            num_sccs=num_sccs,
            rho=rho,
            density=density,
        )
