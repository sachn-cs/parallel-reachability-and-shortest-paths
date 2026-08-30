"""NetworkX adapter for reachq graphs.

Requires ``networkx``. Install with ``pip install reachq[research]``.

Provides bidirectional conversion between reachq Digraphs and
NetworkX DiGraphs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reachq.graph import Digraph


def to_networkx(graph: Digraph) -> Any:
    """Convert a reachq Digraph to a NetworkX DiGraph.

    Args:
        graph: The input digraph.

    Returns:
        A ``networkx.DiGraph`` with the same vertices and edges.

    Raises:
        ImportError: If ``networkx`` is not installed.
    """
    try:
        import networkx as nx
    except ImportError as e:
        raise ImportError(
            "networkx is required for NetworkX interop. "
            "Install with: pip install reachq[research]"
        ) from e

    g = nx.DiGraph()
    for v in graph.vertices():
        g.add_node(v)
    for u, v in graph.edges():
        g.add_edge(u, v)
    return g


def from_networkx(nx_graph: Any) -> Digraph:
    """Convert a NetworkX graph to a reachq Digraph.

    Args:
        nx_graph: A ``networkx.DiGraph`` (or any object with
            ``nodes()`` and ``edges()`` methods).

    Returns:
        The reconstructed Digraph.

    Raises:
        ImportError: If ``networkx`` is not installed.
    """
    from importlib.util import find_spec

    if find_spec("networkx") is None:
        raise ImportError(
            "networkx is required for NetworkX interop. "
            "Install with: pip install reachq[research]"
        )

    from reachq.graph import Digraph

    g = Digraph()
    for v in nx_graph.nodes():
        g.add_vertex(v)
    for u, v in nx_graph.edges():
        g.add_edge(u, v)
    return g
