from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from finance_agent.analysis import audit
from finance_agent.ingest import read_statement_csv
from finance_agent.reporting import load_agreement_caps, render_markdown


app = typer.Typer(add_completion=False, help="Fee Forensics: bank fee + interest audit agent.")
console = Console()


@app.command("audit")
def audit_cmd(
    statement_csv: Path = typer.Argument(..., exists=True, readable=True, help="Statement export CSV"),
    out: Path = typer.Option(
        Path("reports/report.md"), "--out", "-o", help="Output Markdown report path"
    ),
    agreement: Path
    | None = typer.Option(None, "--agreement", help="Optional agreement/terms text file"),
    flag_threshold_abs: float = typer.Option(
        25.0, "--flag-threshold", help="Flag single fee/interest debits >= this amount"
    ),
) -> None:
    """
    Audit a statement CSV and produce a negotiation-ready Markdown report.
    """
    txns = read_statement_csv(statement_csv)
    rep = audit(txns, flag_threshold_abs=flag_threshold_abs)
    caps = load_agreement_caps(agreement) if agreement else None

    md = render_markdown(rep, agreement=caps)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")

    console.print(f"[bold green]Wrote report:[/bold green] {out}")
    console.print(
        f"Fees: [bold]{rep.fee_total:,.2f}[/bold] | Interest: [bold]{rep.interest_total:,.2f}[/bold] | Debits: {rep.total_debits:,.2f}"
    )


@app.command()
def schema() -> None:
    """
    Print expected CSV columns.
    """
    console.print("Minimum columns (case-insensitive): date/transaction_date, description/memo, amount")


if __name__ == "__main__":
    app()

