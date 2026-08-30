"""Arrow IPC serialisation for reachq graphs.

Requires ``pyarrow``. Install with ``pip install reachq[research]``.

Provides zero-copy serialisation of graph adjacency data via Arrow
IPC (Feather) format. Useful for interop with Rust/C++ graph libraries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reachq.graph import Digraph


def dump_arrow(graph: Digraph, path: str) -> None:
    """Serialize a Digraph to Arrow IPC format.

    Args:
        graph: The input digraph.
        path: Output file path.

    Raises:
        ImportError: If ``pyarrow`` is not installed.
    """
    try:
        import pyarrow as pa
        from pyarrow import ipc
    except ImportError as e:
        raise ImportError(
            "pyarrow is required for Arrow serialisation. "
            "Install with: pip install reachq[research]"
        ) from e

    vertices = list(graph.vertices())
    edges = list(graph.edges())

    v_array = pa.array(vertices)
    u_array = pa.array([u for u, _ in edges])
    v_edge_array = pa.array([v for _, v in edges])

    table = pa.table(
        {
            "vertices": v_array,
            "edge_src": u_array,
            "edge_dst": v_edge_array,
        }
    )

    with ipc.new_file(path, table.schema) as writer:
        writer.write_table(table)


def load_arrow(path: str) -> Digraph:
    """Deserialize a Digraph from Arrow IPC format.

    Args:
        path: Input file path (must be an Arrow IPC file written by
            ``dump_arrow``).

    Returns:
        The reconstructed Digraph.

    Raises:
        ImportError: If ``pyarrow`` is not installed.
    """
    try:
        from pyarrow import ipc
    except ImportError as e:
        raise ImportError(
            "pyarrow is required for Arrow serialisation. "
            "Install with: pip install reachq[research]"
        ) from e

    from reachq.graph import Digraph

    reader = ipc.open_file(path)
    table = reader.read_all()

    g = Digraph()
    for v in table["vertices"]:
        g.add_vertex(v.as_py())
    for u, v in zip(table["edge_src"], table["edge_dst"]):
        g.add_edge(u.as_py(), v.as_py())
    return g
