"""Download SNAP datasets used by the benchmarks.

Idempotent: re-running with files already in data/ skips the download.

Self-contained: defines the dataset table inline so this script works
even before the reachq package is installed.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

from reachq.config import get_logger

log = get_logger("reachq.download")

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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_one(name: str, dest_dir: Path, *, force: bool = False) -> Path:
    if name not in SNAP_DATASETS:
        raise KeyError(f"Unknown dataset {name!r}; available: {list(SNAP_DATASETS)}")
    info = SNAP_DATASETS[name]
    url = str(info["url"])
    filename = url.rsplit("/", 1)[-1]
    dest = dest_dir / filename
    if dest.exists() and not force:
        size_mb = dest.stat().st_size / (1024 * 1024)
        log.info("skip %s: already cached at %s (%.1f MB)", name, dest, size_mb)
        return dest
    dest_dir.mkdir(parents=True, exist_ok=True)
    log.info("downloading %s from %s", name, url)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(dest)
    size_mb = dest.stat().st_size / (1024 * 1024)
    digest = sha256(dest)
    log.info("done %s: %s (%.1f MB, sha256=%s...)", name, dest, size_mb, digest[:16])
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Download SNAP datasets")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=list(SNAP_DATASETS.keys()),
    )
    parser.add_argument("--dest", default="data")
    parser.add_argument(
        "--force", action="store_true", help="Re-download even if cached"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
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
                log.info("%s\t%s\t%s", name, sha256(path), path)
            else:
                log.warning("%s\tMISSING\t%s", name, path)
        return 0

    for name in args.datasets:
        download_one(name, dest_dir, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
