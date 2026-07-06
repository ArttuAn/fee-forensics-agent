# Architecture

This document describes the system architecture of Fee Forensics.

## Overview

Fee Forensics is a Python-based CLI application that analyzes bank statements to identify fees, interest charges, and recurring charges. The system follows a modular architecture with clear separation of concerns.

## System Components

### Core Modules

```
finance_agent/
├── __init__.py          # Package initialization and version
├── models.py            # Data models (Transaction, AuditReport, etc.)
├── ingest.py            # Data ingestion (CSV reading)
├── analysis.py          # Fee analysis and audit logic
├── reporting.py         # Report generation (Markdown, JSON)
├── export.py            # Export functionality
├── cli.py               # Command-line interface
├── lc_explain.py        # LangChain integration for explanations
└── logging_config.py    # Logging configuration
```

### Module Responsibilities

#### `models.py`
- Defines data structures using dataclasses
- `Transaction`: Represents a single bank transaction
- `AuditReport`: Contains audit results and metadata
- `Cap`: Represents fee cap from agreement
- Type hints for all models

#### `ingest.py`
- Reads CSV bank statements
- Parses transaction data
- Validates transaction fields
- Returns list of Transaction objects

#### `analysis.py`
- Core audit logic
- Identifies fees and interest charges
- Detects recurring patterns
- Flags suspicious transactions
- Calculates totals and summaries

#### `reporting.py`
- Generates Markdown reports
- Extracts caps from agreement text
- Formats audit results for display
- Supports agreement-based reporting

#### `export.py`
- Exports audit results as JSON
- Includes metadata and versioning
- Structured output for programmatic use

#### `cli.py`
- Typer-based CLI interface
- Commands: audit, demo, explain
- Error handling and user feedback
- File I/O operations

#### `lc_explain.py`
- LangChain integration
- LLM-powered explanations
- Tracing via LangSmith
- Optional AI features

#### `logging_config.py`
- Logging setup and configuration
- Console and file logging
- Configurable log levels

## Data Flow

```
┌─────────────┐
│ CSV Statement│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   ingest    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Transactions│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  analysis   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Audit Report │
└──────┬──────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Markdown │  │   JSON   │  │  Console │
└──────────┘  └──────────┘  └──────────┘
```

## Design Principles

### 1. Separation of Concerns
Each module has a single, well-defined responsibility. This makes the codebase easier to test, maintain, and extend.

### 2. Type Safety
All functions use type hints. The `py.typed` marker enables type checking for users of the package.

### 3. Data Validation
Input validation occurs at ingestion time. Invalid transactions are rejected early in the pipeline.

### 4. Immutable Data
Dataclasses are used for immutable data structures. This prevents accidental mutations and improves predictability.

### 5. Extensibility
The modular design allows for:
- New data formats (add new ingest functions)
- New report formats (add new reporting functions)
- New analysis rules (extend analysis module)
- New CLI commands (extend cli module)

## Error Handling

### Validation Errors
- Occur during data ingestion
- Raise descriptive exceptions
- Include context about the error

### Runtime Errors
- Caught at CLI level
- User-friendly error messages
- Graceful degradation where possible

## Testing Strategy

### Unit Tests
- Test individual functions in isolation
- Mock external dependencies
- Cover edge cases and error conditions

### Integration Tests
- Test end-to-end workflows
- Use real sample data
- Verify complete pipelines

### Coverage Target
- Current: ~81%
- Target: 90%+

## Performance Considerations

### CSV Reading
- Uses pandas for efficient CSV parsing
- Handles large files with streaming if needed

### Analysis
- O(n) complexity for transaction processing
- Efficient pattern detection using pandas

### Report Generation
- String-based operations
- Minimal memory overhead

## Security Considerations

### Input Sanitization
- All file paths are validated
- No code execution from user input

### Data Privacy
- No data leaves the local system
- Optional LangChain features require explicit opt-in
- Sensitive data is not logged

### Dependency Management
- Regular security audits via bandit
- Dependency vulnerability checks via pip-audit
- Pinned dependency versions

## Deployment Options

### Local Installation
- pip install from source
- Virtual environment recommended

### Docker
- Containerized environment
- Consistent dependencies
- Easy deployment

### Development
- tox for multi-version testing
- pre-commit hooks for code quality
- Makefile for common tasks

## Future Architecture Improvements

### Planned Enhancements
1. **Plugin System**: Allow custom analysis rules
2. **Configuration Files**: YAML/TOML for settings
3. **Database Backend**: Store historical audits
4. **API Layer**: REST API for integrations
5. **Web UI**: Browser-based interface
6. **Caching**: Improve performance for repeated audits

### Scalability Considerations
- Support for very large statement files
- Parallel processing for multiple statements
- Distributed processing for enterprise use

## Dependencies

### Core Dependencies
- `pandas`: Data manipulation
- `python-dateutil`: Date parsing
- `rich`: Terminal formatting
- `typer`: CLI framework

### Optional Dependencies
- `langchain`: AI features
- `langsmith`: AI tracing

### Development Dependencies
- `pytest`: Testing
- `pytest-cov`: Coverage
- `ruff`: Linting and formatting
- `bandit`: Security scanning
- `pip-audit`: Dependency auditing
- `pre-commit`: Git hooks

## Contributing

When contributing to the architecture:
1. Maintain separation of concerns
2. Add type hints to new functions
3. Write tests for new features
4. Update this document for significant changes
5. Follow existing code style and patterns
