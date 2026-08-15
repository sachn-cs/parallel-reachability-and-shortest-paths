# Benchmarks

reachq includes benchmark scripts for evaluating shortcut set and hopset
construction across varying graph sizes, densities, and parameters.

## Important Caveats

- Benchmarks measure observed wall-clock time, not theoretical work or depth.
- We do **not** claim empirical validation proves asymptotic bounds.
- Python is sequential; parallel span bounds are NOT DETERMINED.
- Results are for sanity checking and reproducibility, not for performance
  claims.

## Reachability Benchmarks

```bash
python -m scripts.cli benchmark-reachability \
    --sizes 20 50 100 200 \
    --densities 0.1 0.3 0.5 0.8 \
    --omega 3.0 \
    --seed 42 \
    --output reachability_results.csv
```

### Output Fields

| Field | Description |
|-------|-------------|
| n | Number of vertices |
| m | Number of edges |
| density | Target edge density |
| omega | Matrix multiplication exponent |
| beta_target | Target hopbound from paper formula |
| shortcut_size | Number of shortcut edges produced |
| elapsed_sec | Wall-clock construction time |
| max_hops_observed | Maximum hops from source 0 with shortcuts |
| simulated_work | Coarse simulated work estimate |

## Shortest-Path Benchmarks

```bash
python -m scripts.cli benchmark-shortest-paths \
    --sizes 20 50 100 \
    --epsilons 0.05 0.1 0.2 0.5 \
    --seed 42 \
    --output shortest_paths_results.csv
```

### Output Fields

| Field | Description |
|-------|-------------|
| n | Number of vertices |
| m | Number of edges |
| epsilon | Approximation factor |
| beta_target | Target hopbound |
| hopset_size | Number of hopset edges produced |
| elapsed_sec | Wall-clock construction time |
| max_ratio_observed | Largest observed distance ratio |
| mismatches | Number of vertices violating (1+ε) bound |
| simulated_work | Coarse simulated work estimate |

## Interpreting Results

- **Construction time** grows roughly linearly with m for fixed density, but
  hidden constants from recursion and TC-Pruning can be large.
- **Shortcut/hopset size** should grow sub-quadratically; dense graphs will
  produce larger sets.
- **Max hops observed** should be consistent with beta_target up to constant
  factors.
- **Mismatches** should be zero for hopsets; non-zero indicates a bug.

## Reproducibility

All benchmark scripts accept `--seed` for deterministic graph generation and
algorithm execution. Reported results should be reproducible on the same
hardware and Python version.

## AIRS-bench / ASV

The `benchmarks/` directory at the repo root contains an
[AIRS-bench](https://github.com/airs-bench/airs-bench) suite driven by
[asv](https://asv.readthedocs.io/) (configuration:
`asv.conf.json`). Use `asv run` to track the construction time of
the JLS shortcut-set and CFR hopset across commits. The bench
suite is orthogonal to the ad-hoc CLI benchmarks above; it
automates the runs and emits an HTML report.

The ASV suite produces a configurable list of inputs (n, density, ω)
and benchmarks each algorithm once per revision. Useful for
regression detection across releases.
