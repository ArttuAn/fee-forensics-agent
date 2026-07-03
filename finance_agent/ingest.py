from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from dateutil import parser as date_parser

from finance_agent.models import Transaction


def _first_present_column(df: pd.DataFrame, candidates: list[str]) -> str:
    """Find the first column from candidates that exists in the DataFrame.
    
    Args:
        df: DataFrame to search for columns
        candidates: List of column names to try (case-insensitive)
        
    Returns:
        The actual column name from the DataFrame
        
    Raises:
        ValueError: If none of the candidate columns are found
    """
    lower_to_orig = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_to_orig:
            return lower_to_orig[cand.lower()]
    raise ValueError(f"Missing required column; tried: {candidates}. Found: {list(df.columns)}")


def _parse_date(value: object) -> date:
    """Parse a date value from various formats.
    
    Args:
        value: Date value (Timestamp, string, or other parseable format)
        
    Returns:
        Parsed date object
        
    Raises:
        ValueError: If value is empty or cannot be parsed
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("Empty date")
    if isinstance(value, pd.Timestamp):
        return value.date()
    return date_parser.parse(str(value)).date()


def _is_blank(value: object) -> bool:
    """Check if a value is blank (None, NaN, or empty string).
    
    Args:
        value: Value to check
        
    Returns:
        True if value is blank, False otherwise
    """
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    return str(value).strip() == ""


def _float_or_zero(value: object) -> float:
    """Convert value to float, returning 0.0 for blank values.
    
    Args:
        value: Value to convert
        
    Returns:
        Float value, or 0.0 if blank
    """
    if _is_blank(value):
        return 0.0
    return float(value)


def _resolve_amount_columns(df: pd.DataFrame) -> tuple[str, str, str | None]:
    """Determine if CSV uses single amount column or split debit/credit columns.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Tuple of (mode, primary_col, secondary_col) where mode is 'single' or 'split'
        
    Raises:
        ValueError: If no amount columns can be found
    """
    try:
        amount_col = _first_present_column(df, ["amount", "amt", "value"])
        return "single", amount_col, None
    except ValueError:
        debit_col = _first_present_column(
            df,
            ["debit", "debits", "withdrawal", "withdrawals", "out", "money out"],
        )
        credit_col = _first_present_column(
            df,
            ["credit", "credits", "deposit", "deposits", "in", "money in"],
        )
        return "split", debit_col, credit_col


def _row_amount(row: pd.Series, mode: str, amount_col: str, credit_col: str | None) -> float:
    """Calculate transaction amount from a row based on column mode.
    
    Args:
        row: DataFrame row containing transaction data
        mode: 'single' for single amount column, 'split' for debit/credit columns
        amount_col: Primary column name (amount or debit)
        credit_col: Credit column name (only used in split mode)
        
    Returns:
        Transaction amount (positive for credit, negative for debit)
    """
    if mode == "single":
        return float(row[amount_col])
    assert credit_col is not None
    debit = _float_or_zero(row[amount_col])
    credit = _float_or_zero(row[credit_col])
    return credit - debit


def read_statement_csv(path: str | Path) -> list[Transaction]:
    """Read and parse a bank statement CSV file.
    
    Supports flexible column naming for date, description, and amount fields.
    Handles both single amount columns and split debit/credit columns.
    
    Args:
        path: Path to the CSV file
        
    Returns:
        List of Transaction objects
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the CSV is empty, has no valid transactions, or has invalid data
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    df = pd.read_csv(p)
    if df.empty:
        raise ValueError(f"No transactions found in {p}")

    date_col = _first_present_column(df, ["date", "transaction_date", "posting_date"])
    desc_col = _first_present_column(df, ["description", "memo", "details", "narrative"])
    amount_mode, primary_col, secondary_col = _resolve_amount_columns(df)

    txns: list[Transaction] = []
    for row_idx, row in df.iterrows():
        if amount_mode == "single":
            if _is_blank(row[date_col]) and _is_blank(row[primary_col]):
                continue
        elif (
            _is_blank(row[date_col])
            and _is_blank(row[primary_col])
            and _is_blank(row[secondary_col])
        ):
            continue

        try:
            txn_date = _parse_date(row[date_col])
            description = "" if _is_blank(row[desc_col]) else str(row[desc_col]).strip()
            amount = _row_amount(row, amount_mode, primary_col, secondary_col)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid row {row_idx + 2} in {p}: {exc}") from exc

        if amount == 0.0 and not description:
            continue

        txns.append(Transaction(txn_date=txn_date, description=description, amount=amount))

    if not txns:
        raise ValueError(f"No valid transactions found in {p}")
    return txns
