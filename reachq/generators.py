"""Deterministic graph generators for experiments.

All generators accept an optional random_seed and use seeded random.Random
instances for reproducibility. None of these generators rely on external
libraries.
"""

from __future__ import annotations

import random

from reachq.graph import Digraph, WeightedDigraph


__all__ = [
    "SNAP_BASE",
    "SNAP_DATASETS",
    "complete_dag",
    "cycle_graph",
    "dense_graph",
    "erdos_renyi_digraph",
    "graph_stats",
    "graph_with_sccs",
    "grid_graph",
    "hamming_graph",
    "layered_dag",
    "load_dataset",
    "paley_graph",
    "parse_snap_file",
    "path_graph",
    "petersen_graph",
    "random_dag",
    "shrikhande_cayley",
    "shrikhande_graph",
    "weighted_dense_graph",
    "weighted_path_graph",
    "weighted_random_dag",
]


def path_graph(n: int) -> Digraph:
    """Create a directed path on n vertices: 0 → 1 → ... → n-1.

    Args:
        n: Number of vertices.

    Returns:
        A Digraph with ``n`` vertices and ``n - 1`` edges.
    """
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    return g


def cycle_graph(n: int) -> Digraph:
    """Create a directed cycle on n vertices: 0 → 1 → ... → n-1 → 0.

    Args:
        n: Number of vertices (must be >= 1).

    Returns:
        A Digraph with ``n`` vertices and ``n`` edges forming a
        single SCC of size ``n``.
    """
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        g.add_edge(i, (i + 1) % n)
    return g


def complete_dag(n: int) -> Digraph:
    """Create a complete DAG: edges i → j for all i < j.

    Args:
        n: Number of vertices.

    Returns:
        A Digraph with ``n(n-1)/2`` edges and diameter ``n-1``.
    """
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        for j in range(i + 1, n):
            g.add_edge(i, j)
    return g


def layered_dag(
    layers: list[int],
    edge_probability: float = 0.3,
    random_seed: int | None = None,
) -> Digraph:
    """Create a layered DAG with given layer sizes.

    Args:
        layers: List where layers[i] is the number of vertices in layer i.
        edge_probability: Probability of adding an edge between consecutive
            layers. Edges always go from layer i to layer i+1.
        random_seed: Optional seed for reproducibility.

    Returns:
        A Digraph with vertices named (layer, index).
    """
    rng = random.Random(random_seed)
    g = Digraph()
    vertices: list[list[tuple[int, int]]] = []
    for layer_idx, size in enumerate(layers):
        layer_vertices = []
        for j in range(size):
            v = (layer_idx, j)
            g.add_vertex(v)
            layer_vertices.append(v)
        vertices.append(layer_vertices)

    for i in range(len(layers) - 1):
        for u in vertices[i]:
            for v in vertices[i + 1]:
                if rng.random() < edge_probability:
                    g.add_edge(u, v)
    return g


def random_dag(
    n: int,
    edge_probability: float = 0.3,
    random_seed: int | None = None,
) -> Digraph:
    """Create a random DAG by topologically ordering vertices and sampling edges.

    Args:
        n: Number of vertices.
        edge_probability: Probability of edge i → j for i < j.
        random_seed: Optional seed.

    Returns:
        A Digraph with ``n`` vertices; edges are sampled independently
        from the upper-triangular ordered pairs.
    """
    rng = random.Random(random_seed)
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < edge_probability:
                g.add_edge(i, j)
    return g


def erdos_renyi_digraph(
    n: int,
    edge_probability: float = 0.3,
    random_seed: int | None = None,
) -> Digraph:
    """Create a random directed graph (not necessarily acyclic).

    Each ordered pair (u, v) with u != v is included independently
    with probability ``edge_probability``.

    Args:
        n: Number of vertices.
        edge_probability: Edge probability per ordered pair.
        random_seed: Optional seed.

    Returns:
        A Digraph that may contain cycles.
    """
    rng = random.Random(random_seed)
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        for j in range(n):
            if i != j and rng.random() < edge_probability:
                g.add_edge(i, j)
    return g


def dense_graph(
    n: int,
    edge_count: int,
    random_seed: int | None = None,
) -> Digraph:
    """Create a dense digraph with exactly edge_count edges.

    The graph is not guaranteed to be acyclic.

    Args:
        n: Number of vertices.
        edge_count: Number of edges (must be ≤ n*(n-1)).
        random_seed: Optional seed.

    Raises:
        ValueError: If edge_count exceeds n*(n-1).
    """
    max_edges = n * (n - 1)
    if edge_count > max_edges:
        raise ValueError(f"edge_count {edge_count} exceeds max {max_edges} for n={n}")
    rng = random.Random(random_seed)
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)

    all_pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    rng.shuffle(all_pairs)
    selected = all_pairs[:edge_count]
    for u, v in selected:
        g.add_edge(u, v)
    return g


def graph_with_sccs(
    scc_sizes: list[int],
    inter_edge_probability: float = 0.1,
    random_seed: int | None = None,
) -> Digraph:
    """Create a digraph with specified SCC sizes.

    Each SCC is a directed cycle of the given size. Between SCCs, edges are
    sampled with probability inter_edge_probability, respecting a topological
    ordering of SCCs to keep them distinct.

    Args:
        scc_sizes: List of SCC sizes.
        inter_edge_probability: Probability of adding an edge from SCC i to
            SCC j for i < j.
        random_seed: Optional seed.

    Returns:
        A Digraph where SCCs are guaranteed to match scc_sizes.
    """
    rng = random.Random(random_seed)
    g = Digraph()
    sccs: list[list[int]] = []
    next_vertex = 0
    for size in scc_sizes:
        scc = list(range(next_vertex, next_vertex + size))
        next_vertex += size
        sccs.append(scc)
        for v in scc:
            g.add_vertex(v)
        for idx in range(size):
            u = scc[idx]
            v = scc[(idx + 1) % size]
            g.add_edge(u, v)

    for i in range(len(sccs)):
        for j in range(i + 1, len(sccs)):
            for u in sccs[i]:
                for v in sccs[j]:
                    if rng.random() < inter_edge_probability:
                        g.add_edge(u, v)
    return g


def grid_graph(n: int, m: int) -> WeightedDigraph:
    """Create an n × m grid graph with unit weights.

    Vertices are ``(i, j)`` for ``0 <= i < n``, ``0 <= j < m``.
    Edges go right and down with weight 1.

    Args:
        n: Number of rows.
        m: Number of columns.

    Returns:
        A WeightedDigraph with ``n * m`` vertices and unit-weight
        edges from each cell to its right and down neighbour.
    """
    g = WeightedDigraph()
    for i in range(n):
        for j in range(m):
            g.add_vertex((i, j))
            if i + 1 < n:
                g.add_edge((i, j), (i + 1, j), 1)
            if j + 1 < m:
                g.add_edge((i, j), (i, j + 1), 1)
    return g


def weighted_path_graph(
    n: int,
    weight_range: tuple[int, int] = (1, 10),
    random_seed: int | None = None,
) -> WeightedDigraph:
    """Create a weighted directed path on n vertices.

    Edge ``i → i+1`` gets a random integer weight in ``weight_range``.

    Args:
        n: Number of vertices.
        weight_range: Inclusive ``(lo, hi)`` range for integer weights.
        random_seed: Optional seed.

    Returns:
        A WeightedDigraph with ``n`` vertices and ``n - 1`` edges.
    """
    rng = random.Random(random_seed)
    lo, hi = weight_range
    g = WeightedDigraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n - 1):
        w = rng.randint(lo, hi)
        g.add_edge(i, i + 1, w)
    return g


def weighted_random_dag(
    n: int,
    edge_probability: float = 0.3,
    weight_range: tuple[int, int] = (1, 10),
    random_seed: int | None = None,
) -> WeightedDigraph:
    """Create a weighted random DAG.

    Edges ``i → j`` for ``i < j`` are sampled with probability
    ``edge_probability``. Weights are uniform integers in
    ``weight_range``.

    Args:
        n: Number of vertices.
        edge_probability: Probability of edge i → j for i < j.
        weight_range: Inclusive ``(lo, hi)`` range for integer weights.
        random_seed: Optional seed.

    Returns:
        A WeightedDigraph with ``n`` vertices and a random subset of
        upper-triangular ordered pairs as edges.
    """
    rng = random.Random(random_seed)
    lo, hi = weight_range
    g = WeightedDigraph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < edge_probability:
                g.add_edge(i, j, rng.randint(lo, hi))
    return g


def weighted_dense_graph(
    n: int,
    edge_count: int,
    weight_range: tuple[int, int] = (1, 10),
    random_seed: int | None = None,
) -> WeightedDigraph:
    """Create a dense weighted digraph with exactly ``edge_count`` edges.

    Args:
        n: Number of vertices.
        edge_count: Number of edges (must be ``<= n * (n - 1)``).
        weight_range: Inclusive ``(lo, hi)`` range for integer weights.
        random_seed: Optional seed.

    Returns:
        A WeightedDigraph with ``n`` vertices and ``edge_count`` edges,
        each with a uniform-integer weight in ``weight_range``.

    Raises:
        ValueError: If ``edge_count > n * (n - 1)``.
    """
    max_edges = n * (n - 1)
    if edge_count > max_edges:
        raise ValueError(f"edge_count {edge_count} exceeds max {max_edges} for n={n}")
    rng = random.Random(random_seed)
    lo, hi = weight_range
    g = WeightedDigraph()
    for i in range(n):
        g.add_vertex(i)

    all_pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    rng.shuffle(all_pairs)
    selected = all_pairs[:edge_count]
    for u, v in selected:
        g.add_edge(u, v, rng.randint(lo, hi))
    return g


# ---------------------------------------------------------------------------
# Strongly regular graphs (named fixtures) -- Papers 2/3 test fixtures.
#
# An srg(n, k, lam, mu) graph is regular of degree k with lambda common
# neighbours for adjacent pairs and mu for non-adjacent pairs. The
# parameter feasibility condition is k(k - lam - 1) = (n - k - 1) * mu.
# ---------------------------------------------------------------------------


def petersen_graph() -> Digraph:
    """The Petersen graph: srg(10, 3, 0, 1).

    Triangle-free, girth 5, automorphism group S_5 in its natural action.
    Canonical small test case from algebraic graph theory (Paper 3 §1.3).

    Construction (matches NetworkX's nx.petersen_graph):
      * Outer 5-cycle on vertices 0..4: 0-1-2-3-4-0.
      * Inner 5-cycle on vertices 5..9 in pentagram order: 5-7-9-6-8-5.
      * Spokes (0,5), (1,6), (2,7), (3,8), (4,9).

    Note: the inner cycle is NOT a pentagon on {5,6,7,8,9}; it is a
    pentagram (5-cycle on those vertices but with a non-trivial rotation
    of the labels). Using the wrong inner cycle yields a non-isomorphic
    3-regular graph whose spectrum is the prism graph's, not the
    Petersen's.
    """
    g = Digraph()
    for i in range(10):
        g.add_vertex(i)
    outer_cycle = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
    inner_cycle = [(5, 7), (7, 9), (9, 6), (6, 8), (8, 5)]
    spokes = [(0, 5), (1, 6), (2, 7), (3, 8), (4, 9)]
    for u, v in outer_cycle + inner_cycle + spokes:
        g.add_undirected_edge(u, v)
    return g


# Clebsch graph (srg(16, 5, 0, 2)): correctly constructing this requires
# the Cayley-graph construction on Z_2^5 / {x ~ complement(x)}. The naive
# "XOR weight in {0, 4}" definition gives the wrong graph (8 edges
# instead of 40). We omit this generator and recommend hamming_graph(4, 2)
# or shrikhande_graph() as the 16-vertex SRG fixture instead.


# ---------------------------------------------------------------------------
# 16-vertex SRG (16, 6, 2, 2): the rook's graph K_4 □ K_4 below and the
# Shrikhande graph proper (shrikhande_cayley) are TWO cospectral
# non-isomorphic members of this parameter family. Both are implemented.
# ---------------------------------------------------------------------------


def shrikhande_graph() -> Digraph:
    """The 4x4 rook's graph (the standard K_4 ☐ K_4 SRG): srg(16, 6, 2, 2).

    Each vertex is a cell of a 4x4 chessboard; two cells are adjacent iff
    they share a row or column. This is the *rook's* member of the
    srg(16, 6, 2, 2) family; the non-rook (Shrikhande) graph would need a
    Cayley construction we leave as future work.
    """
    g = Digraph()
    for i in range(16):
        g.add_vertex(i)
    # Cells (r, c) and (r, c') are adjacent iff r == r'; cells (r, c) and
    # (r', c) are adjacent iff c == c'. Encoding: cell id = r*4 + c.
    for r in range(4):
        for c in range(4):
            u = r * 4 + c
            for c2 in range(4):
                if c2 != c:
                    v = r * 4 + c2
                    if u < v:
                        g.add_undirected_edge(u, v)
            for r2 in range(4):
                if r2 != r:
                    v = r2 * 4 + c
                    if u < v:
                        g.add_undirected_edge(u, v)
    return g


def shrikhande_cayley() -> Digraph:
    """The Shrikhande graph proper: Cayley construction on Z_4 x Z_4.

    This is the OTHER srg(16, 6, 2, 2) graph, distinct from the rook's
    graph above (cospectral but non-isomorphic). The Cayley graph is
    built on the group Z_4 x Z_4 with the symmetric generator set
    ``S ∪ (-S) = {(1,0), (0,1), (1,1), (3,0), (0,3), (3,3)}``: each
    vertex is adjacent to the six vertices obtained by adding one of
    these six difference vectors.

    Construction: vertices are Z_4 x Z_4 (16 total, encoded as integers
    ``a * 4 + b`` for ``a, b in {0, 1, 2, 3}``). Two vertices ``u = (a, b)``
    and ``v = (c, d)`` are adjacent iff the difference ``((a - c) mod 4,
    (b - d) mod 4)`` lies in the symmetric generator set. The result is
    a 6-regular undirected graph (12 directed edges per vertex when
    counting both directions) that is cospectral but non-isomorphic to
    the 4x4 rook's graph.

    Returns:
        A :class:`Digraph` with 16 vertices and 96 directed edges
        (48 undirected).
    """
    g = Digraph()
    for i in range(16):
        g.add_vertex(i)
    # Symmetric generator set: S ∪ (-S) for S = {(1,0), (0,1), (1,1)}.
    # The negative of (1,0) is (3,0); (0,1)->(0,3); (1,1)->(3,3).
    differences = {(1, 0), (0, 1), (1, 1), (3, 0), (0, 3), (3, 3)}
    for a in range(4):
        for b in range(4):
            u = a * 4 + b
            for da, db in differences:
                c, d = (a + da) % 4, (b + db) % 4
                v = c * 4 + d
                if u < v:
                    g.add_edge(u, v)
                    g.add_edge(v, u)
    return g


def paley_graph(q: int) -> Digraph:
    """The Paley graph of order q (q prime, q ≡ 1 mod 4).

    Vertex set Z_q; u ~ v iff u - v is a quadratic residue mod q.

    Args:
        q: A prime with ``q ≡ 1 (mod 4)``.

    Returns:
        A Digraph with ``q`` vertices.

    Raises:
        ValueError: If ``q`` is not a prime or ``q ≢ 1 (mod 4)``.
    """
    if q <= 0 or (q - 1) % 4 != 0:
        raise ValueError(f"Paley graph requires q ≡ 1 (mod 4), got q={q}")
    if not _is_prime(q):
        raise ValueError(
            f"paley_graph: only prime q supported (got q={q}). "
            f"Generalisation to prime powers requires finite-field machinery."
        )
    residues = {(x * x) % q for x in range(1, q)}
    g = Digraph()
    for i in range(q):
        g.add_vertex(i)
    for u in range(q):
        for v in range(u + 1, q):
            d = (u - v) % q
            if d in residues:
                g.add_undirected_edge(u, v)
    return g


def _is_prime(n: int) -> bool:
    """Return True iff ``n`` is a prime number.

    Used by ``paley_graph`` to validate the prime ``q`` argument.
    Trial division up to sqrt(n); fine for small n used in fixtures.
    """
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


# ---------------------------------------------------------------------------
# Hamming graph -- Paper 2/3 test fixture.
# Vertices are tuples in {0, ..., q-1}^d; edges connect vertices that
# differ in exactly one coordinate. Cayley-graph structure with the
# elementary vectors as generating set.
# ---------------------------------------------------------------------------


def hamming_graph(d: int, q: int) -> Digraph:
    """The Hamming graph H(d, q).

    ``|V| = q^d``, degree = ``d * (q - 1)``. Vertex labels are
    tuples ``(x_1, ..., x_d)`` mapped to integers via the natural
    mapping ``(x_1, ..., x_d) -> sum x_i * q^(i-1)``.

    Args:
        d: Number of dimensions (>= 1).
        q: Alphabet size (>= 2).

    Returns:
        A Digraph with ``q^d`` vertices.

    Raises:
        ValueError: If ``d < 1`` or ``q < 2``.
    """
    if d < 1:
        raise ValueError(f"hamming_graph: d must be >= 1, got {d}")
    if q < 2:
        raise ValueError(f"hamming_graph: q must be >= 2, got {q}")
    n = q**d
    g = Digraph()
    for i in range(n):
        g.add_vertex(i)
    # Neighbours: differ in exactly one coordinate.
    for v in range(n):
        coords = _int_to_base_q(v, q, d)
        for c in range(d):
            for new_value in range(q):
                if new_value == coords[c]:
                    continue
                new_coords = list(coords)
                new_coords[c] = new_value
                u = _base_q_to_int(new_coords, q)
                if u < v:
                    g.add_undirected_edge(u, v)
    return g


def _int_to_base_q(v: int, q: int, d: int) -> list[int]:
    """Convert integer to base-q representation with d digits (LSB at index 0)."""
    out = [0] * d
    for i in range(d):
        out[i] = v % q
        v //= q
    return out


def _base_q_to_int(coords: list[int], q: int) -> int:
    """Convert base-q digit list (LSB at index 0) back to integer."""
    v = 0
    for i, x in enumerate(coords):
        v += x * (q**i)
    return v


SNAP_BASE = "https://snap.stanford.edu/data"
SNAP_DATASETS: dict[str, dict[str, str | int]] = {
    "cit-HepPh": {
        "url": f"{SNAP_BASE}/cit-HepPh.txt.gz",
        "nodes": 34546,
        "edges": 421578,
        "type": "citation",
    },
    "p2p-Gnutella31": {
        "url": f"{SNAP_BASE}/p2p-Gnutella31.txt.gz",
        "nodes": 62586,
        "edges": 147892,
        "type": "p2p",
    },
    "soc-Epinions1": {
        "url": f"{SNAP_BASE}/soc-Epinions1.txt.gz",
        "nodes": 75879,
        "edges": 508837,
        "type": "social",
    },
    "web-NotreDame": {
        "url": f"{SNAP_BASE}/web-NotreDame.txt.gz",
        "nodes": 325729,
        "edges": 1497134,
        "type": "web",
    },
    "web-Stanford": {
        "url": f"{SNAP_BASE}/web-Stanford.txt.gz",
        "nodes": 281903,
        "edges": 2312497,
        "type": "web",
    },
    "web-Google": {
        "url": f"{SNAP_BASE}/web-Google.txt.gz",
        "nodes": 875713,
        "edges": 5105039,
        "type": "web",
    },
}


def parse_snap_file(path: str) -> Digraph:
    """Parse a SNAP edge list file into a Digraph.

    Each non-comment line is interpreted as ``u v`` (whitespace-
    separated); the resulting graph has directed edges ``u → v``.

    Args:
        path: Path to a SNAP edge list file (optionally ``.gz``).

    Returns:
        A Digraph with integer vertex labels.
    """
    import gzip

    g = Digraph()
    open_fn = gzip.open if path.endswith(".gz") else open
    with open_fn(path, "rt") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                u, v = int(parts[0]), int(parts[1])
                g.add_edge(u, v)
    return g


def load_dataset(name: str, cache_dir: str = "data") -> Digraph:
    """Load a SNAP dataset by name, downloading to cache_dir if needed.

    Args:
        name: One of the keys in SNAP_DATASETS (e.g. "cit-HepPh").
        cache_dir: Directory for cached downloads.

    Returns:
        A Digraph with integer vertex labels.

    Raises:
        KeyError: If name is not in SNAP_DATASETS.
    """
    import urllib.request
    from pathlib import Path

    if name not in SNAP_DATASETS:
        raise KeyError(f"Unknown dataset {name!r}; available: {list(SNAP_DATASETS)}")

    info = SNAP_DATASETS[name]
    url = str(info["url"])
    filename = url.rsplit("/", 1)[-1]
    dest = Path(cache_dir) / filename

    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {name} from {url}...")
        urllib.request.urlretrieve(url, dest)
        print(f"Saved to {dest}")

    return parse_snap_file(str(dest))


def graph_stats(graph: Digraph) -> dict[str, int]:
    """Return basic statistics for a graph.

    Args:
        graph: The input digraph.

    Returns:
        Mapping with keys ``n`` (vertices), ``m`` (edges),
        ``max_out_degree``, ``max_in_degree``.
    """
    return {
        "n": graph.num_vertices(),
        "m": graph.num_edges(),
        "max_out_degree": max(
            (graph.degree_out(v) for v in graph.vertices()), default=0
        ),
        "max_in_degree": max((graph.degree_in(v) for v in graph.vertices()), default=0),
    }
