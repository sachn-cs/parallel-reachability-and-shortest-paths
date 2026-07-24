.PHONY: test test-slow lint typecheck bench docs clean

test:
	pytest -x -q

test-slow:
	pytest -x -q --timeout=300

lint:
	ruff check reachq tests scripts
	ruff format --check reachq tests scripts

format:
	ruff format reachq tests scripts

typecheck:
	mypy reachq

bench:
	python -m benchmarks.bench_jls_construction

docs:
	mkdocs build --strict

clean:
	rm -rf build dist *.egg-info .mypy_cache .ruff_cache .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
