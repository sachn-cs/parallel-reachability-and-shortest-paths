"""Reproducibility test across processes.

Spawns child Python processes with distinct ``PYTHONHASHSEED``
values and asserts byte-identical shortcut/hopset outputs.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from reachq.shortcut import build_shortcut_set_for_reachability
from reachq.graph import Digraph


REPO_ROOT = Path(__file__).parent.parent


SCRIPT = textwrap.dedent(
    """
    import sys
    sys.path.insert(0, %r)
    from reachq.shortcut import build_shortcut_set_for_reachability
    from reachq.graph import Digraph

    g = Digraph()
    for i in range(20):
        g.add_vertex(i)
    for i in range(19):
        g.add_edge(i, i + 1)
    H, beta, _ = build_shortcut_set_for_reachability(
        g, omega=3.0, random_seed=42
    )
    print(repr(sorted(H)))
    print(beta)
    """
    % str(REPO_ROOT)
)


@pytest.mark.parametrize(
    "seed", ["0", "1", "2", "3", "4", "random"]
)
def test_shortcut_set_byte_stable_under_hash_seeds(seed):
    """Two subprocess runs with the same PYTHONHASHSEED must produce
    identical shortcut sets, and the output must be stable across
    diverse hash seeds.
    """
    cmd = [sys.executable, "-c", SCRIPT]
    env = {**os.environ, "PYTHONHASHSEED": seed}
    outputs = []
    for _ in range(2):
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            check=True,
            text=True,
        )
        outputs.append((result.stdout, result.returncode))
    assert outputs[0][0] == outputs[1][0], (
        f"PYTHONHASHSEED={seed}: shortcut set unstable across runs"
    )


def test_default_subprocess_shortcuts_match_main_process():
    """The main process and a subprocess must produce identical
    shortcuts on the same graph, seed, and (default) hash seed.
    """
    g = Digraph()
    for i in range(15):
        g.add_vertex(i)
        if i > 0:
            g.add_edge(i - 1, i)
    main_shortcuts, main_beta, _ = build_shortcut_set_for_reachability(
        g, omega=3.0, random_seed=42
    )

    code = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, '{REPO_ROOT}')
        from reachq.shortcut import build_shortcut_set_for_reachability
        from reachq.graph import Digraph
        g = Digraph()
        for i in range(15):
            g.add_vertex(i)
            if i > 0:
                g.add_edge(i - 1, i)
        H, beta, _ = build_shortcut_set_for_reachability(
            g, omega=3.0, random_seed=42
        )
        print(repr(sorted(H)))
        print(beta)
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONHASHSEED": "0"},
        capture_output=True,
        check=True,
        text=True,
    )
    sub_shortcuts_str = result.stdout.splitlines()[0]
    sub_beta_str = result.stdout.splitlines()[1]
    sub_shortcuts = eval(sub_shortcuts_str)
    sub_beta = float(sub_beta_str)
    assert set(main_shortcuts) == set(sub_shortcuts)
    assert main_beta == sub_beta
