"""Command-line interface for reachq.

The console-script entry point is ``reachq`` (see
``pyproject.toml``'s ``[project.scripts]``). It dispatches to
subcommands defined in ``reachq/cli/main.py``:

- ``reachability`` / ``shortest-paths``: build and query.
- ``benchmark-reachability`` / ``benchmark-shortest-paths`` /
  ``benchmark-large``: run benchmarks.
- ``generate-graph``: produce a synthetic graph and serialize it.

Run ``reachq --help`` for the full surface.
"""
