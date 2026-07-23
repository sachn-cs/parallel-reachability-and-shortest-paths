"""Download SNAP datasets used by the benchmarks.

Idempotent: re-running with files already in data/ skips the download.

Self-contained: defines the dataset table inline so this script works even
before the prspnsd package is installed.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

SNAP_BASE = "https://snap.stanford.edu/data"
SNAP_DATASETS: dict[str, dict[str, str | int]] = {
    "cit-HepPh": {
        "url": f"{SNAP_BASE}/cit-HepPh.txt.gz",
        "nodes": 34546, "edges": 421578, "type": "citation",
    },
    "p2p-Gnutella31": {
        "url": f"{SNAP_BASE}/p2p-Gnutella31.txt.gz",
        "nodes": 62586, "edges": 147892, "type": "p2p",
    },
    "soc-Epinions1": {
        "url": f"{SNAP_BASE}/soc-Epinions1.txt.gz",
        "nodes": 75879, "edges": 508837, "type": "social",
    },
    "web-NotreDame": {
        "url": f"{SNAP_BASE}/web-NotreDame.txt.gz",
        "nodes": 325729, "edges": 1497134, "type": "web",
    },
    "web-Stanford": {
        "url": f"{SNAP_BASE}/web-Stanford.txt.gz",
        "nodes": 281903, "edges": 2312497, "type": "web",
    },
    "web-Google": {
        "url": f"{SNAP_BASE}/web-Google.txt.gz",
        "nodes": 875713, "edges": 5105039, "type": "web",
    },
}


def _sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of *path*."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_one(name: str, dest_dir: Path, *, force: bool = False) -> Path:
    """Download a single SNAP dataset if not already present.

    Returns the path to the cached file.
    """
    if name not in SNAP_DATASETS:
        raise KeyError(f"Unknown dataset {name!r}; available: {list(SNAP_DATASETS)}")
    info = SNAP_DATASETS[name]
    url = str(info["url"])
    filename = url.rsplit("/", 1)[-1]
    dest = dest_dir / filename
    if dest.exists() and not force:
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"[skip] {name}: already cached at {dest} ({size_mb:.1f} MB)", flush=True)
        return dest
    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"[get ] {name}: downloading from {url}", flush=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(dest)
    size_mb = dest.stat().st_size / (1024 * 1024)
    digest = _sha256(dest)
    print(f"[done] {name}: {dest} ({size_mb:.1f} MB, sha256={digest[:16]}...)", flush=True)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Download SNAP datasets")
    parser.add_argument(
        "--datasets", nargs="+", default=list(SNAP_DATASETS.keys()),
        help="Datasets to download (default: all)",
    )
    parser.add_argument(
        "--dest", default="data", help="Destination directory (default: data)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-download even if cached",
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Print sha256 of every cached file and exit",
    )
    args = parser.parse_args()

    dest_dir = Path(args.dest)

    if args.verify:
        for name in args.datasets:
            info = SNAP_DATASETS[name]
            url = str(info["url"])
            filename = url.rsplit("/", 1)[-1]
            path = dest_dir / filename
            if path.exists():
                print(f"{name}\t{_sha256(path)}\t{path}", flush=True)
            else:
                print(f"{name}\tMISSING\t{path}", flush=True)
        return 0

    for name in args.datasets:
        try:
            download_one(name, dest_dir, force=args.force)
        except Exception as e:
            print(f"[fail] {name}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
