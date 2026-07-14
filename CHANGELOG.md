# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CONTRIBUTING.md with development guidelines
- CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
- SECURITY.md with vulnerability reporting policy
- CHANGELOG.md for tracking changes
- .editorconfig for consistent formatting
- .gitattributes for line ending normalization
- .env.example documenting optional configuration
- GitHub issue templates for bug reports and feature requests
- GitHub pull request template
- Dependabot configuration for automated dependency updates
- GitHub funding configuration
- Documentation: getting-started.md, architecture.md, deployment.md, faq.md

### Changed

- Rewrote README.md with improved structure, badges, and comprehensive documentation
- Updated pyproject.toml with corrected metadata and project URLs
- Improved CI workflow with dependency caching and documentation job fixes
- Synced package version with git tags (0.4.0)

### Fixed

- Version mismatch between __init__.py (0.1.0) and git tags (0.4.0)
- CI docs job was a no-op (mkdocs not installed)

## [0.4.0] - 2026-05-20

### Added

- Complete benchmark suite for reachability and shortest paths
- CLI interface for graph generation, shortcut/hopset construction, and queries
- Work/depth simulation model with theoretical bounds tracking
- Invariant checkers for reachability preservation and distance approximation

## [0.3.0] - 2026-05-15

### Added

- Hopset construction with CFR and TruncSSSP-Pruning
- Weighted graph support
- A* search algorithm
- Truncated Dijkstra for distance-bounded queries

## [0.2.0] - 2026-05-10

### Added

- Shortcut set construction with JLS and TC-Pruning
- Matrix multiplication-based transitive closure
- Graph generators (path, cycle, DAG, dense, grid, SCC-structured)
- JSON serialization/deserialization

## [0.1.0] - 2026-05-05

### Added

- Initial release
- Core graph data structures (Digraph, WeightedDigraph)
- BFS and reverse BFS reachability
- SCC decomposition (Kosaraju)
- Topological sort
- Dijkstra shortest paths
- Basic test suite

[Unreleased]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sachncs/parallel-reachability-and-shortest-paths/releases/tag/v0.1.0
