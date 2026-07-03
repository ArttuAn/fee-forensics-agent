from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from finance_agent.analysis import AuditReport
from finance_agent.reporting import AgreementCaps, CapBreach, find_cap_breaches


@dataclass(frozen=True)
class AuditExport:
    version: str
    summary: dict[str, float | int | None]
    recurring_fees: list[dict[str, object]]
    by_month: dict[str, dict[str, float]]
    flagged: list[dict[str, object]]
    cap_breaches: list[dict[str, object]] | None


def _fee_share_pct(report: AuditReport) -> float | None:
    """Calculate the percentage of total debits that are bank charges.
    
    Args:
        report: Audit report containing totals
        
    Returns:
        Percentage as float, or None if debits <= 0
    """
    if report.total_debits <= 0:
        return None
    bank_charges = report.fee_total + report.interest_total
    return round(100.0 * bank_charges / report.total_debits, 2)


def _flagged_rows(report: AuditReport) -> list[dict[str, object]]:
    """Convert flagged transactions to dict format for JSON export.
    
    Args:
        report: Audit report containing flagged items
        
    Returns:
        List of dictionaries with transaction details
    """
    rows: list[dict[str, object]] = []
    for c in report.flagged:
        rows.append(
            {
                "date": c.txn.txn_date.isoformat(),
                "category": c.category,
                "amount": round(-c.txn.amount, 2),
                "matched": c.matched,
                "description": c.txn.description,
            }
        )
    return rows


def _breach_rows(breaches: list[CapBreach]) -> list[dict[str, object]]:
    """Convert cap breaches to dict format for JSON export.
    
    Args:
        breaches: List of cap breach objects
        
    Returns:
        List of dictionaries with breach details
    """
    return [asdict(b) for b in breaches]


def build_audit_export(
    report: AuditReport,
    *,
    version: str,
    agreement: AgreementCaps | None = None,
) -> AuditExport:
    """Build a structured export object from an audit report.
    
    Args:
        report: Audit report to export
        version: Package version string
        agreement: Optional agreement caps for breach detection
        
    Returns:
        AuditExport object with all analysis data
    """
    breaches = find_cap_breaches(report, agreement) if agreement else None
    return AuditExport(
        version=version,
        summary={
            "total_credits": report.total_credits,
            "total_debits": report.total_debits,
            "fee_total": report.fee_total,
            "interest_total": report.interest_total,
            "fee_share_of_debits_pct": _fee_share_pct(report),
            "recurring_fee_count": len(report.recurring_fees),
            "flagged_count": len(report.flagged),
            "cap_breach_count": len(breaches) if breaches is not None else None,
        },
        recurring_fees=[asdict(r) for r in report.recurring_fees],
        by_month=report.by_month,
        flagged=_flagged_rows(report),
        cap_breaches=_breach_rows(breaches) if breaches is not None else None,
    )


def render_json(
    report: AuditReport,
    *,
    version: str,
    agreement: AgreementCaps | None = None,
) -> str:
    """Render an audit report as JSON.
    
    Args:
        report: Audit report to render
        version: Package version string
        agreement: Optional agreement caps for breach detection
        
    Returns:
        JSON string with all analysis data
    """
    payload = build_audit_export(report, version=version, agreement=agreement)
    return json.dumps(asdict(payload), indent=2) + "\n"
