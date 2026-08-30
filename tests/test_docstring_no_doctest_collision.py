"""Regression test for the --doctest-modules flag.

`pyproject.toml` enables ``--doctest-modules`` in pytest's addopts.
The doctest plugin runs every docstring through Python's
parser; any token that looks like a Python expression
(e.g. ``O(n^2)``) is evaluated, and expressions that fail to
evaluate break the collection of an entire test file.

This test greps every docstring under ``reachq/`` for
collision-prone patterns and asserts none of them are present
outside of backtick-quoted form.
"""

from __future__ import annotations

import os
import re

import pytest

import reachq


REACHQ_DIR = os.path.dirname(reachq.__file__)

# Tokens that pytest's doctest plugin would attempt to evaluate.
# Each pattern matches the bare, unquoted form (outside backticks).
FORBIDDEN_TOKENS = [
    re.compile(r"O\(n\^[\d.]+"),         # O(n^2), O(n^1.5)
    re.compile(r"O\(n\*"),                 # O(n*rho)
    re.compile(r"^O\(n\)$", re.MULTILINE),  # O(n) on its own line
    re.compile(r"O\(n\s*\*\s*sqrt"),     # O(n * sqrt(...))
]


def _docstring_tokens(path: str) -> list[str]:
    """Yield forbidden token matches found in a single .py file's docstrings."""
    with open(path) as fp:
        text = fp.read()
    if '"""' not in text:
        return []
    # Crude docstring extraction: split on triple-quote boundaries.
    parts = text.split('"""')
    for chunk in parts[1::2]:  # every other chunk is inside a docstring
        # Strip backticks: a token in `...` is RST-quoted, not Python.
        stripped = re.sub(r"`[^`\n]*`", "", chunk)
        for pattern in FORBIDDEN_TOKENS:
            for match in pattern.finditer(stripped):
                yield match.group()


@pytest.mark.parametrize(
    "relpath",
    [
        os.path.join(dp, f)
        for dp, _, files in os.walk(REACHQ_DIR)
        for f in files
        if f.endswith(".py") and "__pycache__" not in dp
    ],
)
def test_no_doctest_collision_tokens(relpath: str) -> None:
    """No bare ``O(n^...)`` or ``O(n*...)`` tokens in any docstring."""
    matches = list(_docstring_tokens(relpath))
    assert not matches, (
        f"{relpath} contains a forbidden doctest-collision token: "
        f"{matches}. Quote with backticks or use a different symbol."
    )
