# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CONTRIBUTING.md with development guidelines ([#4])
- CODE_OF_CONDUCT.md (Contributor Covenant v2.1) ([#4])
- SECURITY.md with vulnerability reporting policy ([#4])
- CHANGELOG.md for tracking changes ([#4])
- .editorconfig for consistent formatting ([#4])
- .gitattributes for line ending normalization ([#4])
- .env.example documenting optional configuration ([#4])
- GitHub issue templates for bug reports and feature requests ([#4])
- GitHub pull request template ([#4])
- Dependabot configuration for automated dependency updates ([#5])
- GitHub funding configuration ([#5])
- Documentation: getting-started.md, architecture.md, deployment.md, faq.md ([#4])

### Changed

- Rewrote README.md with improved structure, badges, and comprehensive documentation ([#4])
- Updated pyproject.toml with corrected metadata and project URLs ([#4])
- Improved CI workflow with dependency caching and documentation job fixes ([#4])
- Synced package version with git tags (0.4.0) ([#4])

### Fixed

- Version mismatch between \_\_init\_\_.py (0.1.0) and git tags (0.4.0) ([#4])
- CI docs job was a no-op (mkdocs not installed) ([#4])

## [0.5.0] - 2026-07-22

### Added

- Graph base class with template method pattern (`initialize_vertex`, `iterate_edges_from`, `store_edge`, `create_empty`) ([e4ba761])
- Covariant return types on Digraph/WeightedDigraph overrides ([e4ba761])
- ~47 new tests across generators, graph, invariants, serialization, and work_depth modules; coverage 94% → 97% ([582442b])

### Changed

- Extracted `partition_by_labels` and `contract_sccs` into graph.py for co-location with graph structures ([9e37747], [f03d9d0])
- Indexed shortcut edges by source vertex in `parallel_bfs` for O(1) edge lookup ([9b30ed0])
- Indexed hopset edges by source vertex in `shortest_path_hopbound` for O(1) edge lookup ([a2ba6ba])
- Renamed all underscore-prefixed identifiers to public names across 14 files (~78 sites) ([0abc514])
- Extracted Graph → Digraph → WeightedDigraph inheritance hierarchy with template hooks ([e4ba761])
- Graph base class provides shared operations (induced_subgraph, reversed, copy) via template method pattern ([e4ba761])
- Updated architecture, algorithms, index, and FAQ docs to reflect OO hierarchy and O(1) lookups

### Fixed

- Integer overflow in matrix transitive closure (`np.int8` → `np.int32`) ([203a75c])
- mypy `python_version` updated to 3.12 for runtime numpy stub compatibility ([70f8170])

[Unreleased]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/releases/tag/v0.1.0
[#4]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/pull/4
[#5]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/pull/5
