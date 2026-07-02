Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Running Fee Forensics examples..."

New-Item -ItemType Directory -Force -Path ".\output" | Out-Null

fee-forensics audit "..\sample-data\statement.csv" `
  --agreement "..\sample-data\agreement.txt" `
  --out ".\output\sample-report.md" `
  --json-out ".\output\sample-report.json"

fee-forensics audit "..\sample-data\statement.csv" `
  --flag-threshold 5 `
  --out ".\output\sample-report-threshold-5.md"

Write-Host "Done. See .\output\"
