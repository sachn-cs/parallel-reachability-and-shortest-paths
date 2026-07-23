# Start here

Where you go next depends on what you want to do with reachq.

## I want to use the library

Read [`docs/getting-started.md`](getting-started.md) for installation and a
minimal example. The canonical entry point is
`reachq.build_shortcut_set_for_reachability`.

## I want to understand the algorithms

Read [`docs/PAPER.md`](PAPER.md) for the algorithmic content
(two lemmas from the parallel-reachability literature plus the
contributions layered on top of them). For a shorter overview read
[`docs/WHY.md`](WHY.md).

## I want to add a new algorithm to reachq

Read [`CONTRIBUTING.md`](../CONTRIBUTING.md#adding-a-new-algorithm)
for the pattern. The shortest path from idea to PR is:
1. Implement `reachq/research/<your_algo>.py` with a single public
   function.
2. Re-export from `reachq/__init__.py`.
3. Add 3+ tests in `tests/test_<your_algo>.py`.
4. Document in `docs/<your_algo>.md` with: algorithm, complexity,
   references.

## I want to file a bug or ask a question

Open a GitHub issue. See [`docs/faq.md`](faq.md) for common questions.
