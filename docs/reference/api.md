# API Reference

## Core

### `reachq.core.config`

::: reachq.core.config.RefinementConfig
    options:
      members: [from_dict]

::: reachq.core.config.configure_logging
::: reachq.core.config.get_logger

### `reachq.core.errors`

::: reachq.core.errors.ReachqError
::: reachq.core.errors.ReachqValueError
::: reachq.core.errors.ReachqTypeError
::: reachq.core.errors.ReachqGraphError
::: reachq.core.errors.ReachqBackendError
::: reachq.core.errors.ReachqConfigError

### `reachq.core.algorithm`

::: reachq.core.algorithm.build_shortcut_set_for_reachability
::: reachq.core.algorithm.jls_shortcut_set
::: reachq.core.algorithm.jls_with_tc_pruning

### `reachq.core.hopset`

::: reachq.core.hopset.build_hopset_for_sssp
::: reachq.core.hopset.cfr_hopset
::: reachq.core.hopset.cfr_with_truncsssp_pruning

### `reachq.core.prune`

::: reachq.core.prune.compute_tc_pruning_threshold
::: reachq.core.prune.apply_tc_pruning

## Protocols

### `reachq.proto.graph`

::: reachq.proto.graph.Graph

### `reachq.proto.rng`

::: reachq.proto.rng.RNG

### `reachq.proto.backend`

::: reachq.proto.backend.Backend

### `reachq.proto.store`

::: reachq.proto.store.Store
