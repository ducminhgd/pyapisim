.PHONY: help clean install check format

help:
	@echo "Available commands:"
	@echo "  make clean   - Clean the project by removing cache and temporary files."
	@echo "  make install - Install the project dependencies without development packages."
	@echo "  make check   - Check code formatting using ruff."
	@echo "  make format  - Format code using ruff."

clean:
	uv add pyclean --dev
	uv run pyclean .
	uv run ruff clean

install:
	uv sync --all-groups

check:
	uv run ruff format . --check

format:
	uv run ruff format .

pre-commit: format
	uv sync --no-dev