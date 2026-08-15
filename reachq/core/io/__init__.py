"""Serialization backends for reachq graphs.

Three backends are provided:

- ``json`` (always available): human-readable text, ``dump`` /
  ``load`` for Digraph and ``weighted_dump`` / ``weighted_load``
  for WeightedDigraph. Use this for small to medium graphs and
  for diff-friendliness.
- ``arrow`` (optional, requires ``pyarrow``): columnar binary
  format. Faster for large graphs and well-suited for downstream
  dataframe work.
- ``networkx`` (optional, requires ``networkx``): interop with the
  networkx library. ``to_networkx`` / ``from_networkx`` convert
  between Digraph and ``nx.DiGraph``.

The JSON backend is re-exported from the top-level ``reachq``
package as ``dump`` / ``load`` / ``weighted_dump`` / ``weighted_load``.
"""
