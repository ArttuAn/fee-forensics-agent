# Contributing to Fee Forensics

Thank you for your interest in contributing to Fee Forensics!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ArttuAn/fee-forensics-agent.git
   cd fee-forensics-agent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=finance_agent --cov-report=term-missing
```

## Code Style

This project uses:
- **Ruff** for linting and formatting
- **pytest** for testing

Check code style:
```bash
ruff check .
ruff format --check .
```

Auto-format code:
```bash
ruff format .
```

## Making Changes

1. Create a new branch for your feature or bugfix
2. Make your changes following the existing code style
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request with a clear description

## Project Structure

- `finance_agent/` - Main package code
  - `ingest.py` - CSV parsing and transaction ingestion
  - `analysis.py` - Fee classification and audit logic
  - `reporting.py` - Markdown report generation
  - `cli.py` - Command-line interface
  - `models.py` - Data models
  - `export.py` - JSON export functionality
  - `lc_explain.py` - LangChain integration for explain workflow
- `tests/` - Test suite
- `sample-data/` - Sample statement and agreement files
- `examples/` - Example usage and outputs

## Issues

Please report bugs and feature requests via GitHub Issues.
