param(
    [Parameter(Mandatory = $true)]
    [string]$ScriptPath
)

$inputJson = [Console]::In.ReadToEnd()

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$usePyLauncher = $false
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
    $usePyLauncher = $true
}

if (-not $pythonCmd) {
    Write-Warning "[claudets hooks] Python was not found, so hook $ScriptPath was skipped. Install Python or expose python/py in PATH for full governance checks."
    exit 0
}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonCmd.Source
if ($usePyLauncher) {
    $psi.ArgumentList.Add("-3")
}
$psi.ArgumentList.Add($ScriptPath)
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $psi
[void]$process.Start()
$process.StandardInput.Write($inputJson)
$process.StandardInput.Close()
$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$process.WaitForExit()

if ($stdout) {
    [Console]::Out.Write($stdout)
}
if ($stderr) {
    [Console]::Error.Write($stderr)
}

exit $process.ExitCode
