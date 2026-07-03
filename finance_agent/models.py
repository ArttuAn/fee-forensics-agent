from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Transaction:
    txn_date: date
    description: str
    amount: float
    currency: str | None = None

    def __post_init__(self) -> None:
        """Validate transaction data after initialization."""
        if not isinstance(self.amount, (int, float)):
            raise ValueError(f"Amount must be numeric, got {type(self.amount)}")
        if not isinstance(self.description, str):
            raise ValueError(f"Description must be string, got {type(self.description)}")
        if not self.description.strip():
            raise ValueError("Description cannot be empty or whitespace only")
