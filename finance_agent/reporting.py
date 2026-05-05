from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from finance_agent.analysis import AuditReport


@dataclass(frozen=True)
class AgreementCaps:
    monthly_fee_cap: float | None = None
    wire_fee_cap: float | None = None
    overdraft_fee_cap: float | None = None


_MONEY_RE = re.compile(r"(?P<amt>\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)")


def extract_caps_from_text(text: str) -> AgreementCaps:
    t = text.lower()

    def _cap_near(needle: str) -> float | None:
        i = t.find(needle)
        if i < 0:
            return None
        window = t[i : i + 220]
        m = _MONEY_RE.search(window)
        if not m:
            return None
        return float(m.group("amt").replace(",", ""))

    return AgreementCaps(
        monthly_fee_cap=_cap_near("monthly") or _cap_near("maintenance"),
        wire_fee_cap=_cap_near("wire"),
        overdraft_fee_cap=_cap_near("overdraft") or _cap_near("nsf"),
    )


def load_agreement_caps(path: str | Path | None) -> AgreementCaps | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return extract_caps_from_text(p.read_text(encoding="utf-8", errors="ignore"))


def render_markdown(report: AuditReport, *, agreement: AgreementCaps | None = None) -> str:
    lines: list[str] = []
    lines.append("# Fee Forensics Report")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- **Total credits**: {report.total_credits:,.2f}")
    lines.append(f"- **Total debits**: {report.total_debits:,.2f}")
    lines.append(f"- **Estimated bank fees**: {report.fee_total:,.2f}")
    lines.append(f"- **Estimated interest/penalties**: {report.interest_total:,.2f}")
    lines.append("")

    if agreement:
        lines.append("## Agreement caps (extracted)")
        lines.append("")
        lines.append(f"- **Monthly/maintenance cap**: {agreement.monthly_fee_cap if agreement.monthly_fee_cap is not None else 'n/a'}")
        lines.append(f"- **Wire fee cap**: {agreement.wire_fee_cap if agreement.wire_fee_cap is not None else 'n/a'}")
        lines.append(f"- **Overdraft/NSF cap**: {agreement.overdraft_fee_cap if agreement.overdraft_fee_cap is not None else 'n/a'}")
        lines.append("")

    lines.append("## Monthly breakdown (debits)")
    lines.append("")
    lines.append("| Month | Fees | Interest | Other debits |")
    lines.append("|---|---:|---:|---:|")
    for month, buckets in report.by_month.items():
        lines.append(
            f"| {month} | {buckets.get('fee', 0.0):,.2f} | {buckets.get('interest', 0.0):,.2f} | {buckets.get('other_debits', 0.0):,.2f} |"
        )
    lines.append("")

    lines.append("## Largest single fee/interest items (flagged)")
    lines.append("")
    if not report.flagged:
        lines.append("_None flagged at current threshold._")
    else:
        lines.append("| Date | Category | Amount | Matched | Description |")
        lines.append("|---|---|---:|---|---|")
        for c in report.flagged[:50]:
            lines.append(
                f"| {c.txn.txn_date.isoformat()} | {c.category} | {(-c.txn.amount):,.2f} | {c.matched or ''} | {c.txn.description.replace('|', ' ')} |"
            )
    lines.append("")

    lines.append("## Most common descriptions")
    lines.append("")
    lines.append("| Description (normalized) | Count |")
    lines.append("|---|---:|")
    for desc, n in report.top_descriptions:
        lines.append(f"| {desc.replace('|', ' ')} | {n} |")
    lines.append("")

    lines.append("## Next actions (suggested)")
    lines.append("")
    lines.append("- Ask the bank for a **fee schedule** and confirm which line-items are contractual vs discretionary.")
    lines.append("- Request a **12-month fee waiver review** or relationship pricing tier review if fees are recurring.")
    lines.append("- If interest/penalty-like debits appear, ask for the **rate basis** and the **trigger** (overdraft, late payment, reserve).")
    lines.append("")

    return "\n".join(lines)

