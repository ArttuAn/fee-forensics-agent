from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from finance_agent.analysis import audit, classify_transactions
from finance_agent.ingest import read_statement_csv
from finance_agent.models import Transaction
from finance_agent.reporting import (
    AgreementCaps,
    extract_caps_from_text,
    find_cap_breaches,
    render_markdown,
)


def _txn(day: int, description: str, amount: float) -> Transaction:
    return Transaction(txn_date=date(2026, 1, day), description=description, amount=amount)


def test_audit_sums_fees_and_interest() -> None:
    txns = [
        _txn(1, "MONTHLY FEE", -10.0),
        _txn(2, "INTEREST CHARGE", -2.5),
        _txn(3, "ACH CREDIT", 100.0),
        _txn(4, "GROCERIES", -30.0),
    ]
    rep = audit(txns, flag_threshold_abs=1.0)

    assert rep.total_credits == 100.0
    assert rep.total_debits == 42.5
    assert rep.fee_total == 10.0
    assert rep.interest_total == 2.5
    assert any(c.category == "fee" for c in rep.flagged)
    assert any(c.category == "interest" for c in rep.flagged)


def test_classify_prefers_specific_fee_keywords() -> None:
    classified = classify_transactions([_txn(1, "SWIFT TRANSFER FEE", -40.0)])
    assert classified[0].category == "fee"
    assert classified[0].matched == "transfer fee"


def test_read_statement_csv_sample_data() -> None:
    root = Path(__file__).resolve().parent.parent
    txns = read_statement_csv(root / "sample-data" / "statement.csv")
    assert len(txns) == 12
    rep = audit(txns)
    assert rep.fee_total == 155.75
    assert rep.interest_total == 60.92


def test_read_statement_csv_column_aliases(tmp_path: Path) -> None:
    csv_path = tmp_path / "stmt.csv"
    csv_path.write_text(
        "transaction_date,memo,amt\n2026-01-01,MONTHLY FEE,-12.50\n",
        encoding="utf-8",
    )
    txns = read_statement_csv(csv_path)
    assert len(txns) == 1
    assert txns[0].description == "MONTHLY FEE"


def test_read_statement_csv_skips_blank_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "stmt.csv"
    csv_path.write_text(
        "date,description,amount\n2026-01-01,FEE,-5.00\n,,\n2026-01-02,CREDIT,10.00\n",
        encoding="utf-8",
    )
    txns = read_statement_csv(csv_path)
    assert len(txns) == 2


def test_extract_caps_from_agreement_text() -> None:
    text = "Monthly maintenance fee: $10\nIncoming wire fee: $20\nOverdraft / NSF fee: $30\n"
    caps = extract_caps_from_text(text)
    assert caps.monthly_fee_cap == 10.0
    assert caps.wire_fee_cap == 20.0
    assert caps.overdraft_fee_cap == 30.0


def test_find_cap_breaches_includes_below_flag_threshold() -> None:
    txns = [
        _txn(1, "MONTHLY MAINTENANCE FEE", -15.0),
        _txn(2, "INCOMING WIRE FEE", -25.0),
        _txn(3, "OVERDRAFT FEE", -35.0),
    ]
    rep = audit(txns, flag_threshold_abs=100.0)
    caps = AgreementCaps(monthly_fee_cap=10.0, wire_fee_cap=20.0, overdraft_fee_cap=30.0)
    breaches = find_cap_breaches(rep, caps)
    assert len(breaches) == 3
    cap_types = {b.cap_type for b in breaches}
    assert cap_types == {"monthly/maintenance", "wire", "overdraft/NSF"}


def test_render_markdown_includes_cap_breach_section() -> None:
    txns = [_txn(1, "MONTHLY MAINTENANCE FEE", -15.0)]
    rep = audit(txns, flag_threshold_abs=100.0)
    caps = AgreementCaps(monthly_fee_cap=10.0)
    md = render_markdown(rep, agreement=caps)
    assert "## Possible agreement cap breaches" in md
    assert "MONTHLY MAINTENANCE FEE" in md


def test_cap_breach_does_not_false_positive_on_transfer() -> None:
    txns = [_txn(8, "SWIFT TRANSFER FEE", -40.0)]
    rep = audit(txns, flag_threshold_abs=1.0)
    caps = AgreementCaps(wire_fee_cap=20.0, overdraft_fee_cap=30.0)
    breaches = find_cap_breaches(rep, caps)
    cap_types = {b.cap_type for b in breaches}
    assert cap_types == {"wire"}


def test_read_statement_csv_missing_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("date,description\n2026-01-01,FEE\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required column"):
        read_statement_csv(csv_path)
