"""Serialization and deserialization for digraphs.

Uses JSON for portability. No external dependencies beyond the standard
library.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from prspnsd.graph import Digraph, WeightedDigraph


def _vertex_to_json(v: object) -> Any:
    """Convert a vertex to a JSON-serializable type."""
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (list, tuple)):
        return [_vertex_to_json(x) for x in v]
    raise TypeError(f"Vertex of type {type(v).__name__} is not JSON serializable")


def _vertex_from_json(data: Any) -> object:
    """Convert JSON data back to a vertex."""
    if isinstance(data, list):
        return tuple(_vertex_from_json(x) for x in data)
    return data


def digraph_to_dict(graph: Digraph) -> Dict[str, Any]:
    """Convert an unweighted Digraph to a dict representation."""
    return {
        "type": "Digraph",
        "vertices": [_vertex_to_json(v) for v in graph.vertices()],
        "edges": [
            [_vertex_to_json(u), _vertex_to_json(v)]
            for u, v in graph.edges()
        ],
    }


def weighted_digraph_to_dict(graph: WeightedDigraph) -> Dict[str, Any]:
    """Convert a WeightedDigraph to a dict representation."""
    return {
        "type": "WeightedDigraph",
        "vertices": [_vertex_to_json(v) for v in graph.vertices()],
        "edges": [
            [_vertex_to_json(u), _vertex_to_json(v), w]
            for u, v, w in graph.edges()
        ],
    }


def digraph_from_dict(data: Dict[str, Any]) -> Digraph:
    """Reconstruct a Digraph from a dict."""
    if data.get("type") != "Digraph":
        raise ValueError("Expected type 'Digraph' in serialized data")
    g = Digraph()
    for v in data["vertices"]:
        g.add_vertex(_vertex_from_json(v))
    for edge in data["edges"]:
        u, v = edge
        g.add_edge(_vertex_from_json(u), _vertex_from_json(v))
    return g


def weighted_digraph_from_dict(data: Dict[str, Any]) -> WeightedDigraph:
    """Reconstruct a WeightedDigraph from a dict."""
    if data.get("type") != "WeightedDigraph":
        raise ValueError("Expected type 'WeightedDigraph' in serialized data")
    g = WeightedDigraph()
    for v in data["vertices"]:
        g.add_vertex(_vertex_from_json(v))
    for edge in data["edges"]:
        u, v, w = edge
        g.add_edge(_vertex_from_json(u), _vertex_from_json(v), w)
    return g


def digraph_to_json(graph: Digraph) -> str:
    """Serialize a Digraph to a JSON string."""
    return json.dumps(digraph_to_dict(graph), indent=2)


def weighted_digraph_to_json(graph: WeightedDigraph) -> str:
    """Serialize a WeightedDigraph to a JSON string."""
    return json.dumps(weighted_digraph_to_dict(graph), indent=2)


def digraph_from_json(text: str) -> Digraph:
    """Deserialize a Digraph from a JSON string."""
    data = json.loads(text)
    return digraph_from_dict(data)


def weighted_digraph_from_json(text: str) -> WeightedDigraph:
    """Deserialize a WeightedDigraph from a JSON string."""
    data = json.loads(text)
    return weighted_digraph_from_dict(data)
