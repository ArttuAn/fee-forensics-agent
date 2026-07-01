from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Transaction:
    txn_date: date
    description: str
    amount: float
    currency: str | None = None
