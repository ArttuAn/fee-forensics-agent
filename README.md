# Fee Forensics Agent (MVP)

A niche finance agent that audits bank statements to surface **hidden fees**, **recurring charges**, and **interest-like debits**, and produces a **negotiation-ready** report.

## What it does (today)

- Parses bank statement exports (CSV)
- Classifies likely bank fees / interest charges using deterministic heuristics
- Aggregates by month, category, and counterparty-like patterns
- Generates a Markdown report you can share with your bank/account manager
- Optionally reads an agreement/terms text file and extracts numeric fee caps it can compare against

## Install

Requires Python 3.10+.

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

## Quickstart

Use the included sample statement:

```bash
fee-forensics audit sample-data\statement.csv --out reports\sample-report.md
```

Open the report:

```bash
notepad reports\sample-report.md
```

With agreement text:

```bash
fee-forensics audit sample-data\statement.csv --agreement sample-data\agreement.txt --out reports\report.md
```

## CSV format

Minimum columns (case-insensitive; extra columns ok):

- `date` (or `transaction_date`)
- `description` (or `memo`)
- `amount` (positive = credit, negative = debit)

## Notes / roadmap

- Add PDF statement ingestion
- Add “what to ask the bank” suggestion pack
- Add optional LLM enrichment (fully local/offline or API-backed)
