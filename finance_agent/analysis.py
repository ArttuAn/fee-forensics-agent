from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

from finance_agent.models import Transaction

FEE_KEYWORDS = sorted(
    [
        "fee",
        "service charge",
        "maintenance",
        "account charge",
        "monthly charge",
        "overdraft",
        "nsf",
        "returned item",
        "wire",
        "swift",
        "transfer fee",
        "atm fee",
        "foreign transaction",
        "fx fee",
    ],
    key=len,
    reverse=True,
)

INTEREST_KEYWORDS = sorted(
    [
        "interest",
        "finance charge",
        "late charge",
        "penalty interest",
    ],
    key=len,
    reverse=True,
)

_EMPTY_MONTH_BUCKETS = {"fee": 0.0, "interest": 0.0, "other_debits": 0.0}


def _norm(s: str) -> str:
    """Normalize a string by stripping, lowercasing, and collapsing whitespace.
    
    Args:
        s: String to normalize
        
    Returns:
        Normalized string
    """
    return re.sub(r"\s+", " ", s.strip().lower())


def _month_key(d: date) -> str:
    """Generate a month key string from a date.
    
    Args:
        d: Date object
        
    Returns:
        String in format 'YYYY-MM'
    """
    return f"{d.year:04d}-{d.month:02d}"


@dataclass(frozen=True)
class ClassifiedTransaction:
    txn: Transaction
    category: str  # fee | interest | other
    matched: str | None


@dataclass(frozen=True)
class RecurringFee:
    description: str
    occurrences: int
    months_active: int
    total: float
    average: float


@dataclass(frozen=True)
class AuditReport:
    total_debits: float
    total_credits: float
    fee_total: float
    interest_total: float
    top_descriptions: list[tuple[str, int]]
    by_month: dict[str, dict[str, float]]  # month -> {fee, interest, other_debits}
    flagged: list[ClassifiedTransaction]
    fee_items: list[ClassifiedTransaction]
    recurring_fees: list[RecurringFee]


def classify_transactions(txns: list[Transaction]) -> list[ClassifiedTransaction]:
    """Classify transactions as fee, interest, or other based on keyword matching.
    
    Uses heuristic matching against known fee and interest keywords.
    Fees and interest are only classified if they are debits (negative amounts).
    
    Args:
        txns: List of transactions to classify
        
    Returns:
        List of classified transactions with category and matched keyword
    """
    out: list[ClassifiedTransaction] = []
    for t in txns:
        d = _norm(t.description)
        matched_fee = next((k for k in FEE_KEYWORDS if k in d), None)
        matched_int = next((k for k in INTEREST_KEYWORDS if k in d), None)

        # Heuristic: fees/interest are almost always debits
        if t.amount < 0 and matched_int:
            out.append(ClassifiedTransaction(txn=t, category="interest", matched=matched_int))
        elif t.amount < 0 and matched_fee:
            out.append(ClassifiedTransaction(txn=t, category="fee", matched=matched_fee))
        else:
            out.append(ClassifiedTransaction(txn=t, category="other", matched=None))
    return out


def _find_recurring_fees(fee_items: list[ClassifiedTransaction]) -> list[RecurringFee]:
    """Identify recurring fees that appear in 2+ months.
    
    Args:
        fee_items: List of classified fee transactions
        
    Returns:
        List of recurring fees sorted by total amount (descending)
    """
    grouped: dict[str, list[ClassifiedTransaction]] = defaultdict(list)
    for item in fee_items:
        grouped[_norm(item.txn.description)[:80]].append(item)

    recurring: list[RecurringFee] = []
    for description, items in grouped.items():
        months = {_month_key(i.txn.txn_date) for i in items}
        if len(months) < 2:
            continue
        total = sum(-i.txn.amount for i in items)
        occurrences = len(items)
        recurring.append(
            RecurringFee(
                description=description,
                occurrences=occurrences,
                months_active=len(months),
                total=round(total, 2),
                average=round(total / occurrences, 2),
            )
        )

    return sorted(recurring, key=lambda r: (-r.total, -r.months_active, r.description))


def audit(txns: list[Transaction], *, flag_threshold_abs: float = 25.0) -> AuditReport:
    """Perform a comprehensive audit of bank transactions.
    
    Classifies transactions, calculates totals, identifies recurring fees,
    and flags large fee/interest items.
    
    Args:
        txns: List of transactions to audit
        flag_threshold_abs: Minimum absolute amount to flag as large (default: 25.0)
        
    Returns:
        AuditReport containing all analysis results
    """
    classified = classify_transactions(txns)

    total_debits = sum(-c.txn.amount for c in classified if c.txn.amount < 0)
    total_credits = sum(c.txn.amount for c in classified if c.txn.amount > 0)

    fee_total = sum(-c.txn.amount for c in classified if c.category == "fee")
    interest_total = sum(-c.txn.amount for c in classified if c.category == "interest")

    desc_counter: Counter[str] = Counter()
    by_month: dict[str, dict[str, float]] = defaultdict(lambda: dict(_EMPTY_MONTH_BUCKETS))
    flagged: list[ClassifiedTransaction] = []

    for c in classified:
        desc_counter[_norm(c.txn.description)[:80]] += 1
        m = _month_key(c.txn.txn_date)
        if c.txn.amount < 0:
            if c.category in ("fee", "interest"):
                by_month[m][c.category] += -c.txn.amount
            else:
                by_month[m]["other_debits"] += -c.txn.amount

        if c.category in ("fee", "interest") and (-c.txn.amount) >= flag_threshold_abs:
            flagged.append(c)

    top_descriptions = desc_counter.most_common(15)
    by_month_rounded = {
        k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in sorted(by_month.items())
    }
    fee_items = [c for c in classified if c.category == "fee"]
    recurring_fees = _find_recurring_fees(fee_items)

    return AuditReport(
        total_debits=round(total_debits, 2),
        total_credits=round(total_credits, 2),
        fee_total=round(fee_total, 2),
        interest_total=round(interest_total, 2),
        top_descriptions=top_descriptions,
        by_month=by_month_rounded,
        flagged=sorted(flagged, key=lambda x: (-abs(x.txn.amount), x.txn.txn_date)),
        fee_items=fee_items,
        recurring_fees=recurring_fees,
    )
