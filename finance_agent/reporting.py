from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from finance_agent.analysis import AuditReport, ClassifiedTransaction

_EMPTY_CAP = "n/a"


@dataclass(frozen=True)
class AgreementCaps:
    monthly_fee_cap: float | None = None
    wire_fee_cap: float | None = None
    overdraft_fee_cap: float | None = None


@dataclass(frozen=True)
class CapBreach:
    txn_date: str
    description: str
    amount: float
    cap_type: str
    cap_value: float
    over_by: float


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


def _fmt_cap(value: float | None) -> str:
    return _EMPTY_CAP if value is None else f"{value:,.2f}"


def _contains_term(text: str, term: str) -> bool:
    if " " in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def find_cap_breaches(
    report: AuditReport,
    agreement: AgreementCaps,
) -> list[CapBreach]:
    breaches: list[CapBreach] = []

    def _maybe_add(
        c: ClassifiedTransaction,
        *,
        cap_type: str,
        cap_value: float | None,
        desc_needles: tuple[str, ...],
    ) -> None:
        if cap_value is None or c.category != "fee":
            return
        desc = c.txn.description.lower()
        if not any(_contains_term(desc, n) for n in desc_needles):
            return
        amount = -c.txn.amount
        if amount > cap_value:
            breaches.append(
                CapBreach(
                    txn_date=c.txn.txn_date.isoformat(),
                    description=c.txn.description,
                    amount=amount,
                    cap_type=cap_type,
                    cap_value=cap_value,
                    over_by=round(amount - cap_value, 2),
                )
            )

    fee_items = report.fee_items
    for c in fee_items:
        _maybe_add(
            c,
            cap_type="monthly/maintenance",
            cap_value=agreement.monthly_fee_cap,
            desc_needles=("maintenance", "monthly"),
        )
        _maybe_add(
            c,
            cap_type="wire",
            cap_value=agreement.wire_fee_cap,
            desc_needles=("wire", "swift"),
        )
        _maybe_add(
            c,
            cap_type="overdraft/NSF",
            cap_value=agreement.overdraft_fee_cap,
            desc_needles=("overdraft", "nsf", "returned item"),
        )

    return sorted(breaches, key=lambda b: (-b.over_by, b.txn_date))


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
    bank_charges = report.fee_total + report.interest_total
    if report.total_debits > 0:
        share = 100.0 * bank_charges / report.total_debits
        lines.append(f"- **Bank charges as % of debits**: {share:.1f}%")
    lines.append("")

    if report.recurring_fees:
        lines.append("## Recurring fees (2+ months)")
        lines.append("")
        lines.append("| Description | Months | Occurrences | Total | Avg |")
        lines.append("|---|---:|---:|---:|---:|")
        for fee in report.recurring_fees[:20]:
            lines.append(
                f"| {fee.description.replace('|', ' ')} | {fee.months_active} | "
                f"{fee.occurrences} | {fee.total:,.2f} | {fee.average:,.2f} |"
            )
        lines.append("")

    if agreement:
        lines.append("## Agreement caps (extracted)")
        lines.append("")
        lines.append(f"- **Monthly/maintenance cap**: {_fmt_cap(agreement.monthly_fee_cap)}")
        lines.append(f"- **Wire fee cap**: {_fmt_cap(agreement.wire_fee_cap)}")
        lines.append(f"- **Overdraft/NSF cap**: {_fmt_cap(agreement.overdraft_fee_cap)}")
        lines.append("")

        breaches = find_cap_breaches(report, agreement)
        lines.append("## Possible agreement cap breaches")
        lines.append("")
        if not breaches:
            lines.append("_No fee items exceed extracted caps._")
        else:
            lines.append("| Date | Type | Charged | Cap | Over by | Description |")
            lines.append("|---|---|---:|---:|---:|---|")
            for b in breaches:
                desc = b.description.replace("|", " ")
                lines.append(
                    f"| {b.txn_date} | {b.cap_type} | {b.amount:,.2f} | "
                    f"{b.cap_value:,.2f} | {b.over_by:,.2f} | {desc} |"
                )
        lines.append("")

    lines.append("## Monthly breakdown (debits)")
    lines.append("")
    lines.append("| Month | Fees | Interest | Other debits |")
    lines.append("|---|---:|---:|---:|")
    for month, buckets in report.by_month.items():
        fee = buckets.get("fee", 0.0)
        interest = buckets.get("interest", 0.0)
        other = buckets.get("other_debits", 0.0)
        lines.append(f"| {month} | {fee:,.2f} | {interest:,.2f} | {other:,.2f} |")
    lines.append("")

    lines.append("## Largest single fee/interest items (flagged)")
    lines.append("")
    if not report.flagged:
        lines.append("_None flagged at current threshold._")
    else:
        lines.append("| Date | Category | Amount | Matched | Description |")
        lines.append("|---|---|---:|---|---|")
        for c in report.flagged[:50]:
            desc = c.txn.description.replace("|", " ")
            lines.append(
                f"| {c.txn.txn_date.isoformat()} | {c.category} | "
                f"{(-c.txn.amount):,.2f} | {c.matched or ''} | {desc} |"
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
    lines.append(
        "- Ask the bank for a **fee schedule** and confirm which line-items are "
        "contractual vs discretionary."
    )
    lines.append(
        "- Request a **12-month fee waiver review** or relationship pricing tier "
        "review if fees are recurring."
    )
    lines.append(
        "- If interest/penalty-like debits appear, ask for the **rate basis** and "
        "the **trigger** (overdraft, late payment, reserve)."
    )
    lines.append("")

    return "\n".join(lines)
