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
    return re.sub(r"\s+", " ", s.strip().lower())


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


@dataclass(frozen=True)
class ClassifiedTransaction:
    txn: Transaction
    category: str  # fee | interest | other
    matched: str | None


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


def classify_transactions(txns: list[Transaction]) -> list[ClassifiedTransaction]:
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


def audit(txns: list[Transaction], *, flag_threshold_abs: float = 25.0) -> AuditReport:
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

    return AuditReport(
        total_debits=round(total_debits, 2),
        total_credits=round(total_credits, 2),
        fee_total=round(fee_total, 2),
        interest_total=round(interest_total, 2),
        top_descriptions=top_descriptions,
        by_month=by_month_rounded,
        flagged=sorted(flagged, key=lambda x: (-abs(x.txn.amount), x.txn.txn_date)),
        fee_items=fee_items,
    )
