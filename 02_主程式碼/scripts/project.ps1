param([Parameter(ValueFromRemainingArguments=$true)][string[]]$CommandArguments)
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonExe)) { throw "Run scripts/setup.ps1 first." }
Set-Location -LiteralPath $projectRoot
& $pythonExe -m src @CommandArguments
exit $LASTEXITCODE
