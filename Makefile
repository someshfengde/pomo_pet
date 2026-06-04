.DEFAULT_GOAL := help

WEB_HOST ?= 127.0.0.1
WEB_PORT ?= 4173

.PHONY: help install test test-all run web

help:
	@echo "Pomo Pet commands:"
	@echo "  make install    Install project dependencies"
	@echo "  make test       Run the test suite"
	@echo "  make test-all   Run tests with coverage"
	@echo "  make run        Start the desktop pet app"
	@echo "  make web        Serve the web PWA at http://$(WEB_HOST):$(WEB_PORT)"
	@echo ""
	@echo "Options:"
	@echo "  WEB_HOST=0.0.0.0 WEB_PORT=8000 make web"

install:
	uv sync
	uv pip install -e .

test:
	uv run pytest tests/ -v

test-all:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

run:
	uv run pomo-pet start

web:
	python3 -m http.server $(WEB_PORT) --bind $(WEB_HOST) --directory docs
