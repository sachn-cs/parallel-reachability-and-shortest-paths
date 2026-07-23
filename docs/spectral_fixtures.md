# Test fixtures from algebraic graph theory (Papers 2/3)

This note explains the test fixtures added in `reachq/generators.py`
from Papers 2 (Krupnik, "Contributions in Algebraic Graph Theory") and 3
(Salarian, "Algebraic Graph Theory"). These graphs have known
structural properties that make them useful benchmarks for
reachability and shortcut-set construction.

## Why these graphs?

The JLS shortcut-set construction's asymptotic bound `|H| ≤ O(mρ + nρ²)`
depends on the density `ρ = √n / β`. On graphs with known ρ, we can
predict the empirical `|H|`. The following families have
particularly clean structure:

- **Petersen graph** (srg(10, 3, 0, 1)): the canonical small triangle-
  free graph; girth 5; automorphism group S₅. Used as a
  smoke test.
- **Paley graphs** for prime `q ≡ 1 (mod 4)`: vertex-transitive,
  edge-transitive SRGs with predictable eigenvalues.
- **Shrikhande / rook's graph** (srg(16, 6, 2, 2)): the 4×4 rook's
  graph (Cartesian product K₄ □ K₄); used as the standard SRG with
  parameters (16, 6, 2, 2). The OTHER non-isomorphic srg(16, 6, 2, 2)
  graph (the proper Shrikhande Cayley construction) is left as future
  work.
- **Hamming graphs H(d, q)**: Cayley graphs on `Z_q^d` with
  one-coordinate Hamming-distance adjacency. Algebraically tractable:
  eigenvalues are sums of d Fourier-mode eigenvalues.

## What's in `reachq/generators.py`

| Function | Family | Parameters |
|---|---|---|
| `petersen_graph()` | Petersen | n=10, k=3 |
| `paley_graph(q)` | Paley | q prime, q ≡ 1 mod 4 |
| `shrikhande_graph()` | Rook's (= K₄ □ K₄) | n=16, k=6 |
| `hamming_graph(d, q)` | Hamming | d ≥ 1, q ≥ 2 |

## Spectral cross-check

`reachq/spectrum.py` provides `spectrum(g)` and `spectral_gap(g)`
helpers. `scripts/spectral_check.py` runs each fixture through the
JLS shortcut-set construction and reports `|H|`, `β`, and the
spectral gap. The result is sanity-checked against known published
eigenvalue tables.

## What's deliberately NOT here

- **Clebsch graph** (srg(16, 5, 0, 2)): the correct construction
  requires Cayley tables on Z₂⁵ / {x ~ complement(x)}. We document
  this omission rather than ship a broken generator.
- **Generalised-Hamming graphs** (Paper 2 §4): Cayley graphs on
  `Z_q^n` with non-standard generators. The standard Hamming graphs
  are a special case and included above.
- **Spectral graph determination**: we don't classify graphs by
  spectra; we just verify the generators' spectra match published
  values.