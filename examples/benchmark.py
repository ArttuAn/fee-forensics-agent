#!/usr/bin/env python3
"""
Performance benchmark script for Fee Forensics.
Measures execution time for various operations.
"""

import time
from pathlib import Path
from finance_agent.ingest import read_statement_csv
from finance_agent.analysis import audit
from finance_agent.reporting import render_markdown
from finance_agent.export import render_json


def benchmark_operation(name: str, func) -> float:
    """Benchmark a single operation.
    
    Args:
        name: Name of the operation
        func: Function to benchmark
        
    Returns:
        Execution time in seconds
    """
    start_time = time.perf_counter()
    result = func()
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"{name}: {elapsed:.4f}s")
    return elapsed


def run_benchmarks():
    """Run performance benchmarks on key operations."""
    print("=== Fee Forensics Performance Benchmarks ===\n")
    
    statement_path = Path("sample-data/statement.csv")
    if not statement_path.exists():
        print(f"Error: Statement file not found at {statement_path}")
        return
    
    # Benchmark CSV reading
    def read_csv():
        return read_statement_csv(statement_path)
    
    transactions = benchmark_operation("CSV Reading", read_csv)
    print(f"  Transactions loaded: {len(transactions)}")
    
    # Benchmark audit
    def run_audit():
        return audit(transactions, flag_threshold_abs=25.0)
    
    report = benchmark_operation("Audit Processing", run_audit)
    print(f"  Flagged items: {len(report.flagged)}")
    print(f"  Recurring fees: {len(report.recurring_fees)}")
    
    # Benchmark markdown rendering
    def render_md():
        return render_markdown(report)
    
    benchmark_operation("Markdown Rendering", render_md)
    
    # Benchmark JSON export
    def export_json():
        return render_json(report, version="0.4.0")
    
    benchmark_operation("JSON Export", export_json)
    
    print("\n=== Benchmark Complete ===")


if __name__ == "__main__":
    run_benchmarks()
