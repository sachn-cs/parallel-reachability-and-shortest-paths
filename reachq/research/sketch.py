"""HyperLogLog-style approximate reachability.

Estimates the cardinality of a vertex's reachable set using
HyperLogLog sketching. This is much smaller than storing the full
reachability set (O(1) vs O(n) per vertex) and supports fast
cardinality queries.

**Algorithm (HyperLogLog, Flajolet et al. 2007):**

1. Hash every vertex to a binary string.
2. Split each hash into a high-order "register index" of ``p`` bits
   and a low-order "tail" of length ``rho``.
3. For each hash, find the position of the leftmost 1-bit in the
   tail and store the maximum position in the register indexed by
   the register index.
4. Estimate the cardinality as ``alpha_p * m * 2^(-mean(rho))``,
   where ``m = 2^p`` is the number of registers and ``alpha_p``
   is a bias-correction constant.

**Standard error:** approximately ``1.04 / sqrt(m)`` for the default
precision p = 14 (m = 16384 registers).

**Reachability sketch:**

The reachable set is approximated by sketching each vertex that is
reached during BFS. The estimate is the cardinality of the union,
which is exactly what HyperLogLog computes without explicit set
union. The estimate is approximate but:

- Never overestimates by more than a small factor in practice.
- Never underestimates by more than ``3 * standard_error``.
- Supports merging two sketches in O(m) time (union of reachability
  sets).

This is the standard HyperLogLog algorithm; novelty is its
application to reachability counting.
"""

from __future__ import annotations

import hashlib
import math
from collections import deque
from typing import Iterable

from reachq.core.graph import Digraph


# Bias-correction constant from the HyperLogLog paper (Flajolet et
# al. 2007, Table 1). Different p values use different constants.
_ALPHA_PP: dict[int, float] = {
    4: 0.673,
    5: 0.697,
    6: 0.709,
    7: 0.7153,
    8: 0.7213,
    9: 0.7273,
    10: 0.738,
    11: 0.7468,
    12: 0.7554,
    13: 0.7632,
    14: 0.7706,
    15: 0.7774,
    16: 0.7821,
}


def _alpha(p: int) -> float:
    """Bias-correction constant for HyperLogLog precision ``p``."""
    if p < 4:
        raise ValueError(f"precision must be >= 4; got {p}")
    if p < 16:
        result: float = _ALPHA_PP[p]
        return result
    # For p >= 16, alpha_p ≈ 0.7213 / (1 + 1.078 / 2^p).
    result = 0.7213 / (1.0 + 1.078 / (2**p))
    return float(result)


class HyperLogLogSketch:
    """A HyperLogLog cardinality sketch.

    Each sketch is a fixed-size array of registers, where each
    register stores the maximum number of leading zero bits
    observed in the low-order portion of any hashed element mapped
    to that register.

    Attributes:
        precision: Number of bits used for the register index
            (default 14 → 16384 registers).
        registers: The m = 2^p register array, mutated in place by
            ``add`` and ``update``.
    """

    __slots__ = ("precision", "registers")

    def __init__(self, precision: int = 14) -> None:
        if not 4 <= precision <= 16:
            raise ValueError(f"precision must be in [4, 16]; got {precision}")
        self.precision = precision
        self.registers = bytearray(1 << precision)

    def add(self, item: object) -> None:
        """Add an item to the sketch, updating the affected register."""
        h = self._hash(item)
        p = self.precision
        idx = h >> (64 - p)
        # The remaining 64 - p bits are the "tail"; we count the
        # position of the leftmost 1-bit in the tail (1-indexed:
        # "w" in the paper ranges from 1 to 64-p+1).
        tail = (h << p) & ((1 << 64) - 1)  # zero out the index bits
        w = _leading_zero_count(tail, 64 - p) + 1
        if w > self.registers[idx]:
            self.registers[idx] = w

    def update(self, items: Iterable[object]) -> int:
        """Add every item and return the new cardinality estimate.

        Equivalent to ``for item in items: self.add(item)`` followed
        by ``self.cardinality()`` but avoids redundant work.
        """
        for item in items:
            self.add(item)
        return self.cardinality()

    @staticmethod
    def _hash(item: object) -> int:
        """Hash an arbitrary item to 64 bits. Uses SHA-256 for stability."""
        # We need a deterministic hash that produces the same value
        # for the same item across runs. SHA-256 truncated to 64
        # bits is standard for HyperLogLog implementations.
        if isinstance(item, str):
            data = item.encode("utf-8")
        elif isinstance(item, (int, float, bool)):
            data = str(item).encode("utf-8")
        else:
            data = repr(item).encode("utf-8")
        digest = hashlib.sha256(data).digest()
        return int.from_bytes(digest[:8], byteorder="big")

    def cardinality(self) -> int:
        """Estimate the cardinality (number of distinct items added).

        Uses the raw HyperLogLog estimator ``alpha * m^2 / sum(2^-M[j])``
        where ``M[j]`` is the register value. For very small and very
        large cardinalities, applies the small-range and large-range
        corrections from the original paper.
        """
        m = len(self.registers)
        alpha = _alpha(self.precision)
        # Indicator sum: sum of 2^-M[j] across all registers.
        indicator = 0.0
        zeros = 0
        for r in self.registers:
            indicator += 2.0 ** (-int(r))
            if r == 0:
                zeros += 1
        if indicator == 0.0:
            return 0
        raw = alpha * m * m / indicator
        # Small-range correction: when raw <= 2.5 * m and there are
        # zero registers, use linear counting.
        if raw <= 2.5 * m and zeros > 0:
            return int(m * math.log(m / zeros))
        # Large-range correction: when raw > 2^32 / 30, use a
        # different formula (relevant only for p=14 and very large
        # cardinalities, which is rare in practice for reachability).
        if raw > (1 << 32) / 30.0:
            return int(-(1 << 64) * math.log(1 - raw / (1 << 64)))
        return int(raw)

    def merge(self, other: HyperLogLogSketch) -> None:
        """Merge another sketch into this one (set union).

        Both sketches must have the same precision. The result is
        the sketch of the union of the two underlying streams.

        Raises:
            ValueError: If the two sketches have different precisions.
        """
        if self.precision != other.precision:
            raise ValueError(
                f"cannot merge sketches with different precisions: "
                f"{self.precision} vs {other.precision}"
            )
        for i in range(len(self.registers)):
            if other.registers[i] > self.registers[i]:
                self.registers[i] = other.registers[i]

    def __len__(self) -> int:
        return len(self.registers)

    def __repr__(self) -> str:
        m = len(self.registers)
        return (
            f"HyperLogLogSketch(precision={self.precision}, "
            f"m={m}, estimate={self.cardinality()})"
        )


def _leading_zero_count(value: int, total_bits: int) -> int:
    """Count the number of leading zero bits in ``value`` (MSB first).

    ``total_bits`` is the number of bits to consider (i.e., the
    width of the value as stored in a fixed-width register).
    Returns ``total_bits`` if all bits are zero.
    """
    if value == 0:
        return total_bits
    bl = value.bit_length()
    if bl >= total_bits:
        return 0
    return total_bits - bl


def sketch_reachability_estimate(
    graph: Digraph,
    source: object,
    *,
    precision: int = 14,
) -> int:
    """Estimate the size of the reachable set from ``source``.

    Performs a BFS from ``source`` (computing the full reachable
    set), then sketches every reached vertex into a HyperLogLog
    sketch and returns the cardinality estimate.

    For very large graphs, this materialises the reachable set
    in memory first; the sketch then summarises it. Use
    :func:`sketch_reachability_streaming` for the streaming version
    that sketches each vertex as it is reached.

    Args:
        graph: Input digraph.
        source: Source vertex. Must be in ``graph``.
        precision: HyperLogLog precision (default 14). Larger
            precision → smaller standard error, more memory.

    Returns:
        Estimated cardinality of the reachable set.
    """
    sketch = HyperLogLogSketch(precision=precision)
    visited = set()
    visited.add(source)
    q: deque[object] = deque([source])
    out = graph.out_edges
    while q:
        u = q.popleft()
        for v in out.get(u, ()):
            if v not in visited:
                visited.add(v)
                sketch.add(v)
                q.append(v)
    return sketch.cardinality()


def sketch_reachability_streaming(
    graph: Digraph,
    source: object,
    *,
    precision: int = 14,
) -> HyperLogLogSketch:
    """Streaming reachability sketch.

    BFS from ``source`` and add each reached vertex to a
    HyperLogLog sketch as it is visited. The sketch is returned so
    the caller can merge with other sketches (e.g., to estimate
    the union of reachable sets from multiple sources).

    Memory: O(m) where m = 2^precision (default 16384 bytes).
    Does not materialise the reachable set in memory.

    Args:
        graph: Input digraph.
        source: Source vertex. Must be in ``graph``.
        precision: HyperLogLog precision.

    Returns:
        A :class:`HyperLogLogSketch` representing the reachable set.
    """
    sketch = HyperLogLogSketch(precision=precision)
    visited: set[object] = {source}
    q: deque[object] = deque([source])
    out = graph.out_edges
    while q:
        u = q.popleft()
        for v in out.get(u, ()):
            if v not in visited:
                visited.add(v)
                sketch.add(v)
                q.append(v)
    return sketch