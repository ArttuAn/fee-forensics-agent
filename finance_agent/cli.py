from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from finance_agent.analysis import audit
from finance_agent.ingest import read_statement_csv
from finance_agent.lc_explain import explain_from_report_markdown
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


@app.command("explain")
def explain_cmd(
    report_md: Path = typer.Argument(..., exists=True, readable=True, help="A Fee Forensics Markdown report"),
    out_dir: Path = typer.Option(Path("reports/explain"), "--out-dir", "-o", help="Output folder"),
    provider: str = typer.Option(
        "openai", "--provider", help="LLM provider adapter (currently: openai)"
    ),
    model: str = typer.Option("gpt-4o-mini", "--model", help="LLM model name"),
) -> None:
    """
    Use LangChain to generate an email + checklist from a report.

    LangSmith tracing is supported via environment variables:
      - LANGCHAIN_TRACING_V2=true (or LANGSMITH_TRACING=true)
      - LANGCHAIN_API_KEY=...
      - LANGCHAIN_PROJECT=fee-forensics (optional)
    """
    if provider != "openai":
        raise typer.BadParameter("Only --provider openai is supported in this MVP.")

    try:
        from langchain_openai import ChatOpenAI  # type: ignore
    except Exception as e:  # pragma: no cover
        raise typer.BadParameter(
            "Missing optional dependency for OpenAI. Install with: pip install -e \".[llm]\""
        ) from e

    llm = ChatOpenAI(model=model, temperature=0)
    artifacts = explain_from_report_markdown(report_md, llm=llm)

    out_dir.mkdir(parents=True, exist_ok=True)
    email_path = out_dir / "negotiation-email.txt"
    checklist_path = out_dir / "questions-checklist.md"

    email_path.write_text(artifacts.negotiation_email.strip() + "\n", encoding="utf-8")
    checklist_path.write_text(artifacts.questions_checklist.strip() + "\n", encoding="utf-8")

    console.print(f"[bold green]Wrote:[/bold green] {email_path}")
    console.print(f"[bold green]Wrote:[/bold green] {checklist_path}")


if __name__ == "__main__":
    app()

