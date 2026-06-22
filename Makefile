.PHONY: help clean install lint lint-fix format check fix

help:
	@echo "Available commands:"
	@echo "  make clean     - Remove cache and temporary files."
	@echo "  make install   - Install project dependencies."
	@echo "  make lint      - Check linting + formatting (dry-run)."
	@echo "  make fix       - Auto-fix linting + formatting issues."
	@echo "  make check     - Same as lint."

clean:
	uv run pyclean .
	uv run ruff clean

install:
	uv sync --all-groups

lint:
	uv run ruff format . --check

format:
	uv run ruff format .
