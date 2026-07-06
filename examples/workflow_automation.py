#!/usr/bin/env python3
"""
Workflow automation script for Fee Forensics.
Automates common audit workflows and batch processing.
"""

import argparse
from pathlib import Path
from typing import List

from finance_agent.ingest import read_statement_csv
from finance_agent.analysis import audit
from finance_agent.reporting import render_markdown, extract_caps_from_text
from finance_agent.export import render_json
from finance_agent.config import get_config


def audit_single_file(
    statement_path: Path,
    output_dir: Path,
    agreement_path: Path = None,
    config_path: Path = None,
) -> None:
    """Audit a single statement file.
    
    Args:
        statement_path: Path to statement CSV
        output_dir: Output directory for reports
        agreement_path: Optional path to agreement file
        config_path: Optional path to configuration file
    """
    # Load configuration
    config = get_config(config_path)
    
    # Read statement
    print(f"Processing: {statement_path}")
    transactions = read_statement_csv(statement_path)
    print(f"  Loaded {len(transactions)} transactions")
    
    # Perform audit
    report = audit(
        transactions,
        flag_threshold_abs=config.flag_threshold_abs,
        flag_threshold_pct=config.flag_threshold_pct,
    )
    print(f"  Total fees: ${report.fee_total:.2f}")
    print(f"  Total interest: ${report.interest_total:.2f}")
    print(f"  Flagged items: {len(report.flagged)}")
    
    # Generate reports
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Markdown report
    caps = None
    if agreement_path and agreement_path.exists():
        agreement_text = agreement_path.read_text(encoding="utf-8")
        caps = extract_caps_from_text(agreement_text)
    
    markdown = render_markdown(report, agreement=caps)
    md_path = output_dir / f"{statement_path.stem}-report.md"
    md_path.write_text(markdown, encoding="utf-8")
    print(f"  Markdown report: {md_path}")
    
    # JSON report
    json_output = render_json(report, version="0.5.0")
    json_path = output_dir / f"{statement_path.stem}-report.json"
    json_path.write_text(json_output, encoding="utf-8")
    print(f"  JSON report: {json_path}")


def audit_batch(
    statement_dir: Path,
    output_dir: Path,
    agreement_path: Path = None,
    config_path: Path = None,
) -> None:
    """Audit multiple statement files in a directory.
    
    Args:
        statement_dir: Directory containing statement CSVs
        output_dir: Output directory for reports
        agreement_path: Optional path to agreement file
        config_path: Optional path to configuration file
    """
    # Find all CSV files
    csv_files = list(statement_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {statement_dir}")
        return
    
    print(f"Found {len(csv_files)} statement files")
    
    # Process each file
    for csv_file in csv_files:
        try:
            audit_single_file(csv_file, output_dir, agreement_path, config_path)
            print()
        except Exception as e:
            print(f"  Error processing {csv_file}: {e}")
            print()


def main():
    """Main entry point for workflow automation."""
    parser = argparse.ArgumentParser(
        description="Fee Forensics Workflow Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Single file audit
    single_parser = subparsers.add_parser("single", help="Audit a single statement file")
    single_parser.add_argument("statement", type=Path, help="Path to statement CSV")
    single_parser.add_argument("--output", type=Path, default=Path("reports"), help="Output directory")
    single_parser.add_argument("--agreement", type=Path, help="Path to agreement file")
    single_parser.add_argument("--config", type=Path, help="Path to configuration file")
    
    # Batch audit
    batch_parser = subparsers.add_parser("batch", help="Audit multiple statement files")
    batch_parser.add_argument("directory", type=Path, help="Directory containing statement CSVs")
    batch_parser.add_argument("--output", type=Path, default=Path("reports"), help="Output directory")
    batch_parser.add_argument("--agreement", type=Path, help="Path to agreement file")
    batch_parser.add_argument("--config", type=Path, help="Path to configuration file")
    
    args = parser.parse_args()
    
    if args.command == "single":
        audit_single_file(args.statement, args.output, args.agreement, args.config)
    elif args.command == "batch":
        audit_batch(args.directory, args.output, args.agreement, args.config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
