from finance_agent.analysis import audit
from finance_agent.models import Transaction


def test_audit_sums_fees_and_interest() -> None:
    txns = [
        Transaction(txn_date=__import__("datetime").date(2026, 1, 1), description="MONTHLY FEE", amount=-10.0),
        Transaction(txn_date=__import__("datetime").date(2026, 1, 2), description="INTEREST CHARGE", amount=-2.5),
        Transaction(txn_date=__import__("datetime").date(2026, 1, 3), description="ACH CREDIT", amount=100.0),
        Transaction(txn_date=__import__("datetime").date(2026, 1, 4), description="GROCERIES", amount=-30.0),
    ]
    rep = audit(txns, flag_threshold_abs=1.0)

    assert rep.total_credits == 100.0
    assert rep.total_debits == 42.5
    assert rep.fee_total == 10.0
    assert rep.interest_total == 2.5
    assert any(c.category == "fee" for c in rep.flagged)
    assert any(c.category == "interest" for c in rep.flagged)

