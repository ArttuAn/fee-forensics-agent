from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from finance_agent.analysis import audit
from finance_agent.cli import app
from finance_agent.export import render_json
from finance_agent.ingest import read_statement_csv
from finance_agent.models import Transaction
from finance_agent.reporting import AgreementCaps, render_markdown

runner = CliRunner()


def _txn(day: int, description: str, amount: float, *, month: int = 1) -> Transaction:
    return Transaction(txn_date=date(2026, month, day), description=description, amount=amount)


def test_recurring_fees_detected_across_months() -> None:
    txns = [
        _txn(2, "MONTHLY MAINTENANCE FEE", -15.0, month=1),
        _txn(2, "MONTHLY MAINTENANCE FEE", -15.0, month=2),
        _txn(2, "MONTHLY MAINTENANCE FEE", -15.0, month=3),
        _txn(7, "INCOMING WIRE FEE", -25.0, month=1),
    ]
    rep = audit(txns)
    assert len(rep.recurring_fees) == 1
    assert rep.recurring_fees[0].description == "monthly maintenance fee"
    assert rep.recurring_fees[0].months_active == 3
    assert rep.recurring_fees[0].total == 45.0


def test_render_markdown_includes_recurring_section() -> None:
    txns = [
        _txn(2, "MONTHLY MAINTENANCE FEE", -15.0, month=1),
        _txn(2, "MONTHLY MAINTENANCE FEE", -15.0, month=2),
    ]
    rep = audit(txns)
    md = render_markdown(rep)
    assert "## Recurring fees (2+ months)" in md
    assert "monthly maintenance fee" in md


def test_read_statement_csv_debit_credit_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "stmt.csv"
    csv_path.write_text(
        "date,description,debit,credit\n"
        "2026-01-01,MONTHLY FEE,12.50,\n"
        "2026-01-02,PAYROLL,,2500.00\n",
        encoding="utf-8",
    )
    txns = read_statement_csv(csv_path)
    assert len(txns) == 2
    assert txns[0].amount == -12.5
    assert txns[1].amount == 2500.0


def test_render_json_includes_summary_and_recurring() -> None:
    txns = [
        _txn(2, "MONTHLY MAINTENANCE FEE", -15.0, month=1),
        _txn(2, "MONTHLY MAINTENANCE FEE", -15.0, month=2),
    ]
    rep = audit(txns)
    caps = AgreementCaps(monthly_fee_cap=10.0)
    payload = json.loads(render_json(rep, version="0.1.2", agreement=caps))
    assert payload["summary"]["fee_total"] == 30.0
    assert payload["summary"]["recurring_fee_count"] == 1
    assert payload["cap_breaches"] is not None
    assert len(payload["cap_breaches"]) == 2


def test_cli_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "fee-forensics 0.1.2" in result.stdout


def test_cli_audit_writes_markdown_and_json(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    statement = root / "sample-data" / "statement.csv"
    agreement = root / "sample-data" / "agreement.txt"
    md_out = tmp_path / "report.md"
    json_out = tmp_path / "report.json"

    result = runner.invoke(
        app,
        [
            "audit",
            str(statement),
            "--agreement",
            str(agreement),
            "--out",
            str(md_out),
            "--json-out",
            str(json_out),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert md_out.exists()
    assert json_out.exists()
    assert "## Possible agreement cap breaches" in md_out.read_text(encoding="utf-8")
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["summary"]["cap_breach_count"] > 0


def test_cli_demo_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "demo.md"
    result = runner.invoke(app, ["demo", "--out", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_cli_schema() -> None:
    result = runner.invoke(app, ["schema"])
    assert result.exit_code == 0
    assert "date/transaction_date" in result.stdout
