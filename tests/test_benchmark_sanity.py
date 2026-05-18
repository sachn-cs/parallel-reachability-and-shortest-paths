"""Sanity tests for benchmark scripts.

These tests ensure benchmark scripts execute without crashing on small
inputs and produce sensible output.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


class TestBenchmarkReachability:
    """Sanity tests for benchmark_reachability.py."""

    def test_runs_without_crash(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.benchmark_reachability",
                "--sizes",
                "10",
                "20",
                "--densities",
                "0.2",
                "--seed",
                "1",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "n=" in result.stdout

    def test_csv_output(self, tmp_path):
        csv_path = tmp_path / "reachability.csv"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.benchmark_reachability",
                "--sizes",
                "10",
                "--densities",
                "0.2",
                "--seed",
                "1",
                "--output",
                str(csv_path),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "n," in content
        assert "shortcut_size" in content


class TestBenchmarkShortestPaths:
    """Sanity tests for benchmark_shortest_paths.py."""

    def test_runs_without_crash(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.benchmark_shortest_paths",
                "--sizes",
                "10",
                "20",
                "--epsilons",
                "0.1",
                "--seed",
                "1",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "n=" in result.stdout

    def test_csv_output(self, tmp_path):
        csv_path = tmp_path / "shortest_paths.csv"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.benchmark_shortest_paths",
                "--sizes",
                "10",
                "--epsilons",
                "0.1",
                "--seed",
                "1",
                "--output",
                str(csv_path),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "n," in content
        assert "hopset_size" in content


class TestCliSanity:
    """Sanity tests for cli.py subcommands."""

    def test_reachability(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.cli",
                "reachability",
                "--n",
                "20",
                "--m",
                "50",
                "--seed",
                "1",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "Reachability preserved" in result.stdout

    def test_shortest_paths(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.cli",
                "shortest-paths",
                "--n",
                "20",
                "--m",
                "50",
                "--seed",
                "1",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "mismatches" in result.stdout.lower()

    def test_generate_graph(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.cli",
                "generate-graph",
                "path",
                "--n",
                "5",
                "--seed",
                "1",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "type" in result.stdout
