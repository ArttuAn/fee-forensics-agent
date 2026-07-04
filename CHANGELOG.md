# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-07-04

### Added
- SECURITY.md security policy with vulnerability reporting guidelines
- .editorconfig for consistent editor settings across team
- CODEOWNERS file for code review assignment
- GitHub issue templates (bug report, feature request)
- GitHub pull request template with checklist
- MANIFEST.in for proper package distribution
- Release automation workflow for GitHub releases
- Additional badges to README (MIT license, pre-commit, security, code style)

### Changed
- Updated README badges to show current coverage (81%)
- Improved project documentation and governance

### Security
- Added security policy document
- Added bandit security scanning to CI/CD
- Added pip-audit for dependency vulnerability checking

## [0.2.0] - 2026-07-04

### Added
- LICENSE file (MIT License)
- CONTRIBUTING.md with development guidelines
- CHANGELOG.md for tracking version changes
- Pre-commit hooks configuration for code quality
- requirements.txt and requirements-dev.txt for easier installation
- Makefile with common development tasks
- Comprehensive docstrings to all functions across modules
- Transaction model validation for amount and description fields
- Edge case tests for validation and error handling
- Development section in README with Makefile commands

### Changed
- Updated dependencies to latest stable versions (pandas>=2.2.3, python-dateutil>=2.9.0, rich>=13.9.0, typer>=0.12.5, pytest>=8.3.0, ruff>=0.7.0)
- Improved CI/CD pipeline with security (bandit) and dependency (pip-audit) checks
- Enhanced test coverage from ~65% to 81%
- Added try-catch error handling to CLI commands
- Enhanced type hints across all modules

### Fixed
- Better error handling in CLI commands with graceful exit
- Transaction validation prevents empty/whitespace descriptions and invalid amounts

## [0.1.2] - 2026-01-XX

### Added
- Initial release of Fee Forensics agent
- CSV statement ingestion with flexible column mapping
- Heuristic-based fee and interest classification
- Monthly aggregation and breakdown
- Recurring fee detection
- Agreement cap extraction and breach detection
- Markdown report generation
- JSON export functionality
- LangChain integration for negotiation email generation
- CLI with audit, demo, schema, version, and explain commands
