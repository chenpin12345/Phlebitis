$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $projectRoot
& (Join-Path $projectRoot ".venv\Scripts\python.exe") -m src serve
exit $LASTEXITCODE
