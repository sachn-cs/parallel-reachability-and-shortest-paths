"""Reproduce benchmark results end-to-end.

Pipeline:
  1. Auto-detect hardware + library versions (printed to stdout + saved).
  2. Sample synthetic random DAGs at increasing sizes to validate scaling.
  3. Run SNAP datasets if downloads are present.
  4. Write CSV + Markdown summary to results/.

Honest about every failure: timeouts, OOMs, correctness mismatches all
land in the CSV with the error field set.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# Allow `python scripts/reproduce_results.py` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@contextmanager
def _time_limit(seconds: int) -> Iterator[None]:
    """Raise TimeoutError after *seconds* (POSIX-only, used on CI)."""
    def handler(signum: int, frame: object) -> None:
        raise TimeoutError(f"exceeded {seconds}s timeout")

    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def detect_hardware() -> dict[str, str]:
    """Collect hardware + library info. Never raises."""
    info: dict[str, str] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(terse=True),
        "machine": platform.machine(),
        "processor": platform.processor() or "(unknown)",
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu_count": str(os.cpu_count() or 0),
    }
    try:
        import numpy as np

        info["numpy"] = np.__version__
        info["numpy_blas"] = str(np.show_config().mode if False else _detect_blas(np))
    except Exception as e:
        info["numpy"] = f"(import failed: {e})"
    try:
        import scipy  # noqa: F401

        info["scipy"] = scipy.__version__
    except Exception as e:
        info["scipy"] = f"(import failed: {e})"
    try:
        import psutil  # noqa: F401

        info["ram_gb"] = f"{psutil.virtual_memory().total / (1024 ** 3):.1f}"
    except Exception:
        try:
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
            info["ram_gb"] = f"{int(out) / (1024 ** 3):.1f}"
        except Exception:
            info["ram_gb"] = "(unknown)"
    try:
        import sysconfig

        info["python_compiler"] = sysconfig.get_config_var("CC") or "(unknown)"
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        info["cpu_brand"] = out
    except Exception:
        pass
    return info


def _detect_blas(np_mod: object) -> str:
    """Best-effort BLAS detection from numpy config."""
    try:
        cfg = np_mod.show_config()  # type: ignore[attr-defined]
        for line in str(cfg).splitlines():
            for vendor in ("OpenBLAS", "Accelerate", "MKL", "BLIS", "netlib"):
                if vendor.lower() in line.lower():
                    return vendor
    except Exception:
        pass
    return "(unknown)"


def _csv_path(out_dir: Path, kind: str) -> Path:
    """Return a CSV path under out_dir with stable name."""
    return out_dir / f"{kind}.csv"


def _write_csv(path: Path, rows: list[dict[str, object]], header: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def run_sampling(
    sizes: list[int],
    densities: list[float],
    omega: float,
    epsilon: float,
    seed: int,
    timeout: int,
    flags: dict[str, bool],
    out_dir: Path,
) -> list[dict[str, object]]:
    """Run synthetic random DAGs at increasing n. Skip >timeout, never crash."""
    from prspnsd.generators import random_dag, weighted_random_dag
    from prspnsd.hopset import build_hopset_for_sssp
    from prspnsd.reachability import bfs_reachability, parallel_bfs
    from prspnsd.shortcut_set import build_shortcut_set_for_reachability
    from prspnsd.shortest_paths import dijkstra, shortest_path_hopbound

    rows: list[dict[str, object]] = []
    for n in sizes:
        for density in densities:
            label = f"random_dag_n{n}_d{density}"
            print(f"[sample] {label}", flush=True)

            # reachability
            g = random_dag(n, edge_probability=density, random_seed=seed)
            row: dict[str, object] = {
                "kind": "synthetic-reachability",
                "source": label,
                "n": g.num_vertices(),
                "m": g.num_edges(),
                "omega": omega,
                "epsilon": epsilon,
                "density": density,
                "seed": seed,
                **{f"flag_{k}": v for k, v in flags.items()},
            }
            try:
                with _time_limit(timeout):
                    t0 = time.perf_counter()
                    shortcuts, beta = build_shortcut_set_for_reachability(
                        g, omega=omega, random_seed=seed,
                        flags=flags,
                    )
                    elapsed = time.perf_counter() - t0
                row.update({
                    "beta": round(beta, 3),
                    "shortcut_size": len(shortcuts),
                    "elapsed_sec": round(elapsed, 3),
                })
                # Correctness on small graphs only.
                if n <= 2000:
                    src = next(iter(g.vertices()))
                    original = bfs_reachability(g, src)
                    augmented = parallel_bfs(g, src, shortcuts)
                    row["correct"] = original == augmented
            except TimeoutError as e:
                row["error"] = str(e)
                print(f"  TIMEOUT: {e}", flush=True)
            except Exception as e:
                row["error"] = f"{type(e).__name__}: {e}"
                print(f"  ERROR: {row['error']}", flush=True)
            rows.append(row)

            # shortest paths
            label_w = f"weighted_random_dag_n{n}_d{density}"
            print(f"[sample] {label_w}", flush=True)
            wg = weighted_random_dag(n, edge_probability=density, random_seed=seed)
            wrow: dict[str, object] = {
                "kind": "synthetic-shortest-paths",
                "source": label_w,
                "n": wg.num_vertices(),
                "m": wg.num_edges(),
                "omega": omega,
                "epsilon": epsilon,
                "density": density,
                "seed": seed,
                **{f"flag_{k}": v for k, v in flags.items()},
            }
            try:
                with _time_limit(timeout):
                    t0 = time.perf_counter()
                    hopset, beta = build_hopset_for_sssp(
                        wg, epsilon=epsilon, random_seed=seed,
                        flags=flags,
                    )
                    elapsed = time.perf_counter() - t0
                wrow.update({
                    "beta": round(beta, 3),
                    "hopset_size": len(hopset),
                    "elapsed_sec": round(elapsed, 3),
                })
                if n <= 2000:
                    src = next(iter(wg.vertices()))
                    orig = dijkstra(wg, src)
                    approx = shortest_path_hopbound(wg, hopset, src, max_hops=1000)
                    mismatches = sum(
                        1 for v in wg.vertices()
                        if orig.get(v, float("inf")) < float("inf")
                        and approx.get(v, float("inf")) > (1 + epsilon) * orig[v] + 1e-9
                    )
                    wrow["mismatches"] = mismatches
            except TimeoutError as e:
                wrow["error"] = str(e)
                print(f"  TIMEOUT: {e}", flush=True)
            except Exception as e:
                wrow["error"] = f"{type(e).__name__}: {e}"
                print(f"  ERROR: {wrow['error']}", flush=True)
            rows.append(wrow)

    _write_csv(
        _csv_path(out_dir, "scaling"), rows,
        header=[
            "kind", "source", "n", "m", "omega", "epsilon", "density", "seed",
            "beta", "shortcut_size", "hopset_size", "elapsed_sec",
            "correct", "mismatches", "error",
            *(f"flag_{k}" for k in flags),
        ],
    )
    return rows


def run_snap(
    datasets: list[str], omega: float, epsilon: float, seed: int,
    timeout: int, flags: dict[str, bool], out_dir: Path,
) -> list[dict[str, object]]:
    """Run SNAP datasets. Skips missing files."""
    from prspnsd.generators import load_dataset
    from prspnsd.reachability import bfs_reachability, parallel_bfs
    from prspnsd.shortcut_set import build_shortcut_set_for_reachability

    rows: list[dict[str, object]] = []
    for name in datasets:
        print(f"[snap] {name}", flush=True)
        try:
            g = load_dataset(name)
        except Exception as e:
            rows.append({
                "kind": "snap-reachability", "source": name,
                "error": f"load failed: {e}",
                **{f"flag_{k}": v for k, v in flags.items()},
            })
            print(f"  LOAD FAILED: {e}", flush=True)
            continue

        row: dict[str, object] = {
            "kind": "snap-reachability",
            "source": name,
            "n": g.num_vertices(),
            "m": g.num_edges(),
            "omega": omega,
            "seed": seed,
            **{f"flag_{k}": v for k, v in flags.items()},
        }
        try:
            with _time_limit(timeout):
                t0 = time.perf_counter()
                shortcuts, beta = build_shortcut_set_for_reachability(
                    g, omega=omega, random_seed=seed, flags=flags,
                )
                elapsed = time.perf_counter() - t0
            row.update({
                "beta": round(beta, 3),
                "shortcut_size": len(shortcuts),
                "elapsed_sec": round(elapsed, 3),
            })
            if g.num_vertices() <= 5000:
                src = next(iter(g.vertices()))
                original = bfs_reachability(g, src)
                augmented = parallel_bfs(g, src, shortcuts)
                row["correct"] = original == augmented
        except TimeoutError as e:
            row["error"] = str(e)
            print(f"  TIMEOUT after {timeout}s", flush=True)
        except MemoryError as e:
            row["error"] = f"MemoryError: {e}"
            print("  OOM", flush=True)
        except Exception as e:
            row["error"] = f"{type(e).__name__}: {e}"
            print(f"  ERROR: {row['error']}", flush=True)
        rows.append(row)

    _write_csv(
        _csv_path(out_dir, "snap"), rows,
        header=[
            "kind", "source", "n", "m", "omega", "seed",
            "beta", "shortcut_size", "elapsed_sec", "correct", "error",
            *(f"flag_{k}" for k in flags),
        ],
    )
    return rows


def write_summary(
    out_dir: Path,
    hardware: dict[str, str],
    flags: dict[str, bool],
    scaling: list[dict[str, object]],
    snap: list[dict[str, object]],
) -> None:
    """Write a Markdown summary table."""
    lines: list[str] = []
    lines.append("# Reproduction summary")
    lines.append("")
    lines.append("## Hardware")
    for k, v in hardware.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Active flags")
    for k, v in flags.items():
        lines.append(f"- `{k}` = `{v}`")
    lines.append("")
    lines.append("## Sampling")
    if scaling:
        lines.append("| kind | source | n | m | beta | |H| | time (s) | correct/error |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in scaling:
            err = r.get("error", "")
            ok = r.get("correct")
            cell = "true" if ok is True else ("false" if ok is False else err)
            sz = r.get("shortcut_size", r.get("hopset_size", ""))
            lines.append(
                f"| {r.get('kind','')} | {r.get('source','')} | {r.get('n','')} | "
                f"{r.get('m','')} | {r.get('beta','')} | {sz} | "
                f"{r.get('elapsed_sec','')} | {cell} |"
            )
    lines.append("")
    lines.append("## SNAP")
    if snap:
        lines.append("| kind | source | n | m | beta | |H| | time (s) | correct/error |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in snap:
            err = r.get("error", "")
            ok = r.get("correct")
            cell = "true" if ok is True else ("false" if ok is False else err)
            lines.append(
                f"| {r.get('kind','')} | {r.get('source','')} | {r.get('n','')} | "
                f"{r.get('m','')} | {r.get('beta','')} | {r.get('shortcut_size','')} | "
                f"{r.get('elapsed_sec','')} | {cell} |"
            )
    (out_dir / "summary.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce benchmark results")
    parser.add_argument("--out", default="results", help="Output directory")
    parser.add_argument("--sizes", nargs="+", type=int, default=[200, 500, 1000, 2000, 5000])
    parser.add_argument(
        "--densities", nargs="+", type=float, default=[0.05, 0.1, 0.3],
    )
    parser.add_argument("--datasets", nargs="+", default=None,
                        help="SNAP datasets to run (default: whatever is in data/)")
    parser.add_argument("--omega", type=float, default=3.0)
    parser.add_argument("--epsilon", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout", type=int, default=60,
                        help="Per-run timeout in seconds")
    parser.add_argument(
        "--no-adaptive-sampling", action="store_true",
        help="Disable adaptive sampling probability (Improvement 1)",
    )
    parser.add_argument(
        "--no-label-compress", action="store_true",
        help="Disable label compression (Improvement 2)",
    )
    parser.add_argument(
        "--no-skip-condense", action="store_true",
        help="Disable skip-condensation on DAG inputs (Improvement 3)",
    )
    parser.add_argument(
        "--no-hop-bounded-bfs", action="store_true",
        help="Disable hop-bounded BFS in pivot loop (Improvement 4)",
    )
    parser.add_argument(
        "--no-degree-ordered-pivots", action="store_true",
        help="Disable degree-ordered pivot iteration (Improvement 5)",
    )
    parser.add_argument(
        "--no-tight-tc-trigger", action="store_true",
        help="Disable tightened TC-pruning trigger (Improvement 7)",
    )
    parser.add_argument(
        "--no-skip-trivial-part", action="store_true",
        help="Disable skip-trivial-partition guard (Improvement 6)",
    )
    parser.add_argument(
        "--no-tc-pruning", action="store_true",
        help="Disable TC pruning entirely (baselined comparison)",
    )
    parser.add_argument("--skip-snap", action="store_true")
    parser.add_argument("--skip-sampling", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    hardware = detect_hardware()
    print("=== Hardware ===", flush=True)
    for k, v in hardware.items():
        print(f"  {k}: {v}", flush=True)
    (out_dir / "hardware.json").write_text(json.dumps(hardware, indent=2))

    flags = {
        "adaptive_sampling": not args.no_adaptive_sampling,
        "label_compress": not args.no_label_compress,
        "skip_condense": not args.no_skip_condense,
        "hop_bounded_bfs": not args.no_hop_bounded_bfs,
        "degree_ordered_pivots": not args.no_degree_ordered_pivots,
        "tight_tc_trigger": not args.no_tight_tc_trigger,
        "skip_trivial_part": not args.no_skip_trivial_part,
        "enable_tc_pruning": not args.no_tc_pruning,
    }
    print("=== Active flags ===", flush=True)
    for k, v in flags.items():
        print(f"  {k} = {v}", flush=True)

    scaling: list[dict[str, object]] = []
    snap: list[dict[str, object]] = []

    if not args.skip_sampling:
        print("\n=== Sampling ===", flush=True)
        scaling = run_sampling(
            args.sizes, args.densities, args.omega, args.epsilon,
            args.seed, args.timeout, flags, out_dir,
        )

    if not args.skip_snap:
        from prspnsd.generators import SNAP_DATASETS

        data_dir = Path("data")
        if args.datasets is not None:
            datasets = args.datasets
        else:
            # Anything that's already downloaded.
            datasets = []
            for name, info in SNAP_DATASETS.items():
                fn = str(info["url"]).rsplit("/", 1)[-1]
                if (data_dir / fn).exists():
                    datasets.append(name)
        if datasets:
            print("\n=== SNAP ===", flush=True)
            snap = run_snap(
                datasets, args.omega, args.epsilon, args.seed,
                args.timeout, flags, out_dir,
            )
        else:
            print("\n(no SNAP datasets in data/; run scripts/download_datasets.py first)",
                  flush=True)

    write_summary(out_dir, hardware, flags, scaling, snap)
    print(f"\nWrote {out_dir}/summary.md", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
