#!/usr/bin/env python3
"""
Example script showing how to use Fee Forensics programmatically.
"""

from pathlib import Path
from finance_agent.ingest import read_statement_csv
from finance_agent.analysis import audit
from finance_agent.reporting import render_markdown, extract_caps_from_text
from finance_agent.export import render_json
from finance_agent.config import Config, get_config

# Example 1: Basic audit with config
def basic_audit_example():
    """Perform a basic audit of a bank statement using configuration."""
    print("=== Basic Audit Example ===")

    # Load configuration
    config = get_config()
    print(f"Using threshold: ${config.flag_threshold_abs}")

    # Read the statement
    statement_path = Path("sample-data/statement.csv")
    transactions = read_statement_csv(statement_path)
    print(f"Loaded {len(transactions)} transactions")

    # Perform the audit with config values
    report = audit(
        transactions,
        flag_threshold_abs=config.flag_threshold_abs,
        flag_threshold_pct=config.flag_threshold_pct,
    )

    # Print summary
    print(f"Total fees: ${report.fee_total:.2f}")
    print(f"Total interest: ${report.interest_total:.2f}")
    print(f"Flagged items: {len(report.flagged)}")
    print(f"Recurring fees: {len(report.recurring_fees)}")

    # Generate markdown report
    markdown = render_markdown(report)
    output_path = Path(config.output_dir) / "example-audit.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Report saved to {output_path}")

# Example 2: Audit with agreement caps
def audit_with_agreement_example():
    """Perform an audit with agreement cap checking."""
    print("\n=== Audit with Agreement Example ===")

    # Load configuration
    config = get_config()

    # Read the statement
    statement_path = Path("sample-data/statement.csv")
    transactions = read_statement_csv(statement_path)

    # Perform the audit
    report = audit(
        transactions,
        flag_threshold_abs=config.flag_threshold_abs,
        flag_threshold_pct=config.flag_threshold_pct,
    )

    # Load agreement caps
    agreement_path = Path("sample-data/agreement.txt")
    if agreement_path.exists():
        agreement_text = agreement_path.read_text(encoding="utf-8")
        caps = extract_caps_from_text(agreement_text)

        # Generate report with agreement
        markdown = render_markdown(report, agreement=caps)
        output_path = Path(config.output_dir) / "example-audit-with-agreement.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Report with agreement saved to {output_path}")
    else:
        print("No agreement file found")

# Example 3: JSON export
def json_export_example():
    """Export audit results as JSON."""
    print("\n=== JSON Export Example ===")

    # Load configuration
    config = get_config()

    # Read the statement
    statement_path = Path("sample-data/statement.csv")
    transactions = read_statement_csv(statement_path)

    # Perform the audit
    report = audit(
        transactions,
        flag_threshold_abs=config.flag_threshold_abs,
        flag_threshold_pct=config.flag_threshold_pct,
    )

    # Export as JSON
    json_output = render_json(report, version="0.6.0")
    output_path = Path(config.output_dir) / "example-audit.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json_output, encoding="utf-8")
    print(f"JSON report saved to {output_path}")

# Example 4: Custom configuration
def custom_config_example():
    """Use custom configuration."""
    print("\n=== Custom Configuration Example ===")

    # Create custom config
    config = Config(
        flag_threshold_abs=50.0,
        flag_threshold_pct=0.10,
        output_dir="custom-reports",
    )

    print(f"Custom threshold: ${config.flag_threshold_abs}")

    # Read and audit
    statement_path = Path("sample-data/statement.csv")
    transactions = read_statement_csv(statement_path)
    report = audit(
        transactions,
        flag_threshold_abs=config.flag_threshold_abs,
        flag_threshold_pct=config.flag_threshold_pct,
    )

    # Generate report
    markdown = render_markdown(report)
    output_path = Path(config.output_dir) / "custom-audit.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Custom report saved to {output_path}")

if __name__ == "__main__":
    basic_audit_example()
    audit_with_agreement_example()
    json_export_example()
    custom_config_example()
    print("\n=== Examples completed ===")
