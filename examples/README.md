# Examples

This folder contains practical, copy-pasteable runs and outputs.

## 1) Run the sample end-to-end

```bash
fee-forensics audit ..\sample-data\statement.csv --agreement ..\sample-data\agreement.txt --out output\sample-report.md
```

Open the generated report:

```bash
notepad output\sample-report.md
```

## 2) Lower the flag threshold (see more items)

```bash
fee-forensics audit ..\sample-data\statement.csv --flag-threshold 5 --out output\sample-report-threshold-5.md
```

## 3) Audit your own export

If your bank export has `date`, `description`, `amount` columns:

```bash
fee-forensics audit "C:\path\to\your-statement.csv" --out output\my-report.md
```

If it uses different column names (e.g. `memo`, `transaction_date`), it should still work.
