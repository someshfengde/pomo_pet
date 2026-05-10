.PHONY: install test test-all run

install:
	uv sync
	uv pip install -e .

test:
	uv run pytest tests/ -v

test-all:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

run:
	uv run pomo-pet start
