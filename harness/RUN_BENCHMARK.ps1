param([string]$Python = '', [int]$IdleTimeout = 60)
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'TOKS vs HF v2 | Idle-gated Windows benchmark'
if (-not $Python) {
    $localPython = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) 'work\toks-native\venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $localPython) { $Python = $localPython }
    elseif (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.venv\Scripts\python.exe')) { $Python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe' }
    else { throw 'Run INSTALL_ENV.ps1 with a native Windows CPython 3.12 executable first.' }
}
$runFolder = Join-Path $PSScriptRoot ('runs\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $runFolder | Out-Null
$hostSnapshot = [ordered]@{captured_utc=[DateTime]::UtcNow.ToString('o'); cpu=(Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors); os=(Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber); power_scheme=(& powercfg /getactivescheme | Out-String).Trim()}
$hostSnapshot | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runFolder 'host.json') -Encoding utf8
Start-Transcript -LiteralPath (Join-Path $runFolder 'live.log') | Out-Null
Clear-Host
Write-Host 'TOKS vs HUGGING FACE v2' -ForegroundColor Cyan
Write-Host 'Requires CPU <=10%. Other applications and agents are preserved.'
Write-Host 'Parity and each measured library/trial run in separate processes.'
Write-Host 'Single-thread first-pass headline; repeated text and Python pools in appendix.'
Write-Host ''
& $Python -u (Join-Path $PSScriptRoot 'benchmark.py') --assets $PSScriptRoot --output $runFolder --idle-timeout $IdleTimeout
$benchExit = $LASTEXITCODE
Set-Content -LiteralPath (Join-Path $runFolder 'exit-code.txt') -Value $benchExit
Write-Host "`nExit code: $benchExit. Receipts: $runFolder"
if ($benchExit -eq 3) { Write-Host 'REFUSED: CPU was not consistently idle. No completed result table was produced.' -ForegroundColor Yellow }
elseif ($benchExit -eq 0) {
    & $Python (Join-Path $PSScriptRoot 'audit_results.py') $runFolder
    Set-Content -LiteralPath (Join-Path $runFolder 'audit-exit-code.txt') -Value $LASTEXITCODE
}
Write-Host 'Window left open for screenshots.'
Stop-Transcript | Out-Null
