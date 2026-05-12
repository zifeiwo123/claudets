function Fail($Message) {
    [Console]::Error.WriteLine("[claudets PostToolUse check]`n$Message")
    exit 2
}

$raw = [Console]::In.ReadToEnd()
try {
    $payload = $raw | ConvertFrom-Json
} catch {
    Fail "Cannot parse hook input: $_"
}

$cwd = [string]$payload.cwd
if (-not $cwd) { $cwd = (Get-Location).Path }
$toolInput = $payload.tool_input

$paths = @()
foreach ($key in @("file_path", "path")) {
    if ($toolInput.PSObject.Properties.Name -contains $key) {
        $value = [string]$toolInput.$key
        if ($value) {
            $p = [System.IO.Path]::GetFullPath((Join-Path $cwd $value))
            if ([System.IO.Path]::IsPathRooted($value)) { $p = $value }
            $paths += $p
        }
    }
}

$scanFiles = @()
foreach ($p in $paths) {
    if ((Test-Path $p) -and ([System.IO.Path]::GetExtension($p).ToLowerInvariant() -in @(".py", ".md", ".json", ".yaml", ".yml", ".ps1"))) {
        $scanFiles += $p
    }
}

$checks = @(
    @{ Pattern = 'rets?_net\s*=\s*rets?_\w+\s*\*\s*\(\s*1\s*-'; Message = 'Suspicious multiplicative cost deduction. Prefer raw_ret - turnover * cost_rate.' },
    @{ Pattern = '\.clip\s*\(\s*lower\s*=\s*-?0?\.\d+'; Message = 'Suspicious post-hoc return clipping. Drawdown control must use only prior information.' },
    @{ Pattern = 'dt\.start_time'; Message = 'Weekly strategy dates should use the last real trading day, not period start_time.' },
    @{ Pattern = 'TUSHARE_TOKEN\s*=\s*[''"][A-Za-z0-9_\-]{12,}[''"]'; Message = 'Hard-coded Tushare token detected. Use os.getenv("TUSHARE_TOKEN").' },
    @{ Pattern = 'pool\.update_ic_results\(\{[^:]+:\s*ic_tr'; Message = 'Factor pool appears to store train IC. Store validation IC for selection and direction.' }
)

$problems = @()
foreach ($file in $scanFiles) {
    $text = Get-Content $file -Raw -ErrorAction SilentlyContinue
    foreach ($check in $checks) {
        if ($text -match $check.Pattern) {
            $rel = $file.Replace($cwd, "").TrimStart("\", "/")
            $problems += "$rel`: $($check.Message)"
        }
    }
}

if ($scanFiles | Where-Object { [System.IO.Path]::GetExtension($_).ToLowerInvariant() -eq ".py" }) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    $usePy = $false
    if (-not $python) {
        $python = Get-Command py -ErrorAction SilentlyContinue
        $usePy = $true
    }
    if ($python) {
        Push-Location $cwd
        try {
            if ($usePy) {
                $result = & $python.Source -3 -m compileall -q . 2>&1
            } else {
                $result = & $python.Source -m compileall -q . 2>&1
            }
        } finally {
            Pop-Location
        }
        if ($LASTEXITCODE -ne 0) {
            $problems += "compileall failed:`n$result"
        }
    } else {
        Write-Warning "[claudets hooks] Python not found; compileall skipped."
    }
}

$stateDir = Join-Path $cwd ".claude/state"
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
if ($paths.Count -gt 0) {
    $changed = $paths | ForEach-Object { $_.Replace($cwd, "").TrimStart("\", "/") }
    Set-Content -Path (Join-Path $stateDir "needs_closing_review.txt") -Value ($changed -join "`n") -Encoding UTF8
}

if ($problems.Count -gt 0) {
    Fail (($problems -join "`n`n") + "`n`nFix these governance checks before closing the task.")
}

exit 0
