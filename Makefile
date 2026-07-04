.PHONY: install install-dev test lint format clean demo help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install the package
	pip install -e .

install-dev: ## Install the package with development dependencies
	pip install -e ".[dev]"
	pip install pre-commit

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=finance_agent --cov-report=term-missing --cov-report=html

lint: ## Run linting checks
	ruff check .
	ruff format --check .

format: ## Format code with ruff
	ruff format .

format-check: ## Check code formatting
	ruff format --check .

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

demo: ## Run the demo
	fee-forensics demo

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit hooks on all files
	pre-commit run --all-files

check: lint test ## Run all checks (lint and test)
