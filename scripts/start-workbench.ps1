$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run scripts/setup-workbench.ps1 first.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'web\dist\index.html'))) { throw 'Frontend is not built. Run scripts/setup-workbench.ps1.' }
& $pythonPath -c 'import fastapi, uvicorn, torch, torchvision, ultralytics, transformers, safetensors, sklearn, psutil; from src.workbench.contracts import Experiment'
if ($LASTEXITCODE -ne 0) { throw 'Missing or incompatible dependencies. Run scripts/setup-workbench.ps1 and retry.' }
$occupied = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if ($occupied) {
    Write-Host 'Port 8765 is already in use. If the workbench is running, open http://127.0.0.1:8765.'
    Write-Host 'Otherwise stop the other service or run: .venv\Scripts\python.exe -m src workbench --port 8766'
    return
}
Write-Host 'Phlebitis workbench: http://127.0.0.1:8765'
Write-Host 'Keep this terminal open. Press Ctrl+C to stop the web server. Running workers remain traceable.'
& $pythonPath -m src workbench --port 8765
if ($LASTEXITCODE -ne 0) { throw 'Workbench stopped with an error. Review the message above; do not expose the admin port through a public tunnel.' }
