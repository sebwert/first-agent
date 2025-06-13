# Makefile
.PHONY: install install-dev test lint format pre-commit clean

# Install production dependencies
install:
	uv sync

# Install all dependencies including dev
install-dev:
	uv sync --dev

# Run tests
test:
	uv run pytest tests/ -v

# Run tests with coverage
test-cov:
	uv run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Lint code
lint:
	uv run ruff check .
	uv run mypy src/

# Format code
format:
	uv run ruff format .
	uv run ruff check . --fix

# Run pre-commit on all files
pre-commit:
	uv run pre-commit run --all-files

# Setup pre-commit hooks
setup-hooks:
	uv run pre-commit install

# Clean up cache and temp files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

# Run the main application
run:
	uv run python main.py

# Create new feature branch
feature:
	@read -p "Feature name: " name; \
	git checkout -b feature/$$name

# Bump version
bump-patch:
	uv run python scripts/version.py patch

bump-minor:
	uv run python scripts/version.py minor

bump-major:
	uv run python scripts/version.py major