function Block($Message) {
    [Console]::Error.WriteLine("[claudets PreToolUse blocked]`n$Message")
    exit 2
}

$raw = [Console]::In.ReadToEnd()
try {
    $payload = $raw | ConvertFrom-Json
} catch {
    Block "Cannot parse hook input: $_"
}

$tool = [string]$payload.tool_name
$toolInput = $payload.tool_input
$cwd = [string]$payload.cwd
if (-not $cwd) { $cwd = (Get-Location).Path }

if ($tool -eq "Bash") {
    $cmd = [string]$toolInput.command
    $dangerous = @(
        '\brm\s+-rf\b',
        '\bgit\s+reset\s+--hard\b',
        '\bgit\s+clean\s+-fd\b',
        '\bdel\s+/[sSqQ]\b',
        '\brmdir\s+/[sSqQ]\b',
        '\bRemove-Item\b.*\b-Recurse\b.*\b-Force\b'
    )
    foreach ($pattern in $dangerous) {
        if ($cmd -match $pattern) {
            Block "Dangerous command detected. Confirm backup and impact first:`n$cmd"
        }
    }

    $preflightFlag = Join-Path $cwd ".claude/.preflight_ok"
    $preflightApproved = $false
    if (Test-Path $preflightFlag) {
        $age = (Get-Date) - (Get-Item $preflightFlag).LastWriteTime
        $preflightApproved = $age.TotalSeconds -lt 600
    }

    $longOrWriting = @(
        'python\s+.*autonomous_loop\.py',
        'python\s+.*main\.py',
        'py\s+.*autonomous_loop\.py',
        'py\s+.*main\.py'
    )
    $safeKeywords = @('compileall', '--help', '-h', '--dry-run', 'pytest -q')
    $isLong = $false
    foreach ($pattern in $longOrWriting) {
        if ($cmd -match $pattern) { $isLong = $true }
    }
    $isSafe = $false
    foreach ($keyword in $safeKeywords) {
        if ($cmd.Contains($keyword)) { $isSafe = $true }
    }
    if ($isLong -and -not $isSafe -and -not $preflightApproved) {
        Block "This command may run a long experiment or overwrite report outputs.`nRun /preflight first. It may write report/ and data/weekly_daily_features.parquet.`nCommand: $cmd"
    }
    exit 0
}

if ($tool -in @("Edit", "Write", "MultiEdit")) {
    $path = [string]$toolInput.file_path
    if (-not $path) { $path = [string]$toolInput.path }
    $lowerPath = $path.Replace("\", "/").ToLowerInvariant()

    $protected = @(".env", "/secrets/", "credentials", ".git/", ".db", ".sqlite", ".parquet", "tushare_local", "daily_qfq", "adj_factor")
    foreach ($item in $protected) {
        if ($lowerPath.Contains($item)) {
            Block "Direct edits to secrets, source databases, or parquet data/result files are blocked:`n$path`nUse the pipeline to regenerate derived files."
        }
    }

    $text = ""
    foreach ($key in @("content", "new_string", "old_string")) {
        if ($toolInput.PSObject.Properties.Name -contains $key) {
            $value = [string]$toolInput.$key
            if ($value) { $text += "`n$value" }
        }
    }
    $secretPatterns = @(
        'tushare.*token\s*=\s*[''"][A-Za-z0-9_\-]{12,}[''"]',
        'api[_-]?key\s*=\s*[''"][A-Za-z0-9_\-]{16,}[''"]',
        'secret\s*=\s*[''"][A-Za-z0-9_\-]{16,}[''"]'
    )
    foreach ($pattern in $secretPatterns) {
        if ($text -match $pattern) {
            Block "Content appears to contain a token/api_key/secret. Use environment variables instead."
        }
    }
}

exit 0
