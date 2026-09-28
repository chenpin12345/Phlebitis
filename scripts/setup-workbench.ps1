param([switch]$CpuOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    & (Join-Path $PSScriptRoot 'setup.ps1') -CpuOnly:$CpuOnly
} else {
    & .\.venv\Scripts\python.exe -c 'import torch, torchvision'
    if ($LASTEXITCODE -ne 0) { & (Join-Path $PSScriptRoot 'setup.ps1') -CpuOnly:$CpuOnly }
}
& .\.venv\Scripts\python.exe -m pip --isolated install -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
& .\.venv\Scripts\python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency conflict detected.' }
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'Install Node.js 22 or later, then reopen PowerShell and retry.' }
Push-Location -LiteralPath (Join-Path $projectRoot 'web')
try {
    & npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally { Pop-Location }
Write-Host 'Ready. Run scripts/start-workbench.ps1.'
