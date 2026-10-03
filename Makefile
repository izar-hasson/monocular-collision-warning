UV ?= uv

.PHONY: setup lint format-check typecheck test check hooks

setup:
	$(UV) sync --locked

lint:
	$(UV) run --locked ruff check .

format-check:
	$(UV) run --locked ruff format --check .

typecheck:
	$(UV) run --locked mypy

test:
	$(UV) run --locked pytest -q

check:
	$(MAKE) lint
	$(MAKE) format-check
	$(MAKE) typecheck
	$(MAKE) test

hooks:
	$(UV) run --locked pre-commit install
