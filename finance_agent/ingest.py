from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from dateutil import parser as date_parser

from finance_agent.models import Transaction


def _first_present_column(df: pd.DataFrame, candidates: list[str]) -> str:
    lower_to_orig = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_to_orig:
            return lower_to_orig[cand.lower()]
    raise ValueError(f"Missing required column; tried: {candidates}. Found: {list(df.columns)}")


def _parse_date(value: object) -> date:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("Empty date")
    if isinstance(value, (pd.Timestamp,)):
        return value.date()
    return date_parser.parse(str(value)).date()


def read_statement_csv(path: str | Path) -> list[Transaction]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    df = pd.read_csv(p)

    date_col = _first_present_column(df, ["date", "transaction_date", "posting_date"])
    desc_col = _first_present_column(df, ["description", "memo", "details", "narrative"])
    amt_col = _first_present_column(df, ["amount", "amt", "value"])

    txns: list[Transaction] = []
    for _, row in df.iterrows():
        txn_date = _parse_date(row[date_col])
        description = "" if row[desc_col] is None else str(row[desc_col]).strip()
        amount = float(row[amt_col])
        txns.append(Transaction(txn_date=txn_date, description=description, amount=amount))
    return txns

