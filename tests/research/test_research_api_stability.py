"""Smoke test: every reachq.research module declares ``__experimental__``."""

from __future__ import annotations

import importlib
import os

import pytest

import reachq.research

RESEARCH_DIR = os.path.dirname(reachq.research.__file__)


@pytest.mark.parametrize(
    "name",
    [
        f[:-3]
        for f in os.listdir(RESEARCH_DIR)
        if f.endswith(".py") and f != "__init__.py"
    ],
)
def test_module_marks_experimental(name: str) -> None:
    """Every research module declares ``__experimental__ = True``."""
    mod = importlib.import_module(f"reachq.research.{name}")
    assert getattr(mod, "__experimental__", False) is True, (
        f"reachq.research.{name} is missing the __experimental__ = True marker"
    )


def test_research_init_docstring_warns() -> None:
    """The research package __init__ documents the experimental boundary."""
    assert "experimental" in (reachq.research.__doc__ or "").lower()
