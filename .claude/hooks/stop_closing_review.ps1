$raw = [Console]::In.ReadToEnd()
try {
    $payload = $raw | ConvertFrom-Json
} catch {
    $payload = $null
}

$cwd = if ($payload -and $payload.cwd) { [string]$payload.cwd } else { (Get-Location).Path }
$stateDir = Join-Path $cwd ".claude/state"
$needs = Join-Path $stateDir "needs_closing_review.txt"
$prompted = Join-Path $stateDir "closing_review_prompted.txt"

if ((Test-Path $needs) -and -not (Test-Path $prompted)) {
    $changed = Get-Content $needs -Raw -ErrorAction SilentlyContinue
    Set-Content -Path $prompted -Value "prompted" -Encoding UTF8
    [Console]::Error.WriteLine("[claudets Stop blocked]`nFiles changed in this turn. Before closing, provide:`n1. changed files;`n2. why they changed;`n3. syntax checks or tests run;`n4. whether backtest/report must be rerun;`n5. remaining risks and next steps.`n`nChanged files:`n$changed")
    exit 2
}

Remove-Item $needs -ErrorAction SilentlyContinue
Remove-Item $prompted -ErrorAction SilentlyContinue
exit 0
