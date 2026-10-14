param([string]$PythonCommand = "py", [switch]$CpuOnly)
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    if ($PythonCommand -eq "py") { & py -3.12 -m venv .venv }
    else { & $PythonCommand -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw "Python 3.12 environment creation failed." }
}
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$wheelIndex = "https://download.pytorch.org/whl/cu130"
if ($CpuOnly) { $wheelIndex = "https://download.pytorch.org/whl/cpu" }
& $pythonExe -m pip --isolated install --no-cache-dir torch==2.13.0 torchvision==0.28.0 --index-url $wheelIndex
if ($LASTEXITCODE -ne 0) { throw "PyTorch installation failed." }
$requirementsFile = "requirements-dev.txt"
if (Test-Path -LiteralPath "requirements.lock.txt") { $requirementsFile = "requirements.lock.txt" }
& $pythonExe -m pip --isolated install --no-cache-dir -r $requirementsFile
if ($LASTEXITCODE -ne 0) { throw "Project dependencies installation failed." }
& $pythonExe -m pip check
if ($LASTEXITCODE -ne 0) { throw "Dependency conflict detected." }
& $pythonExe -m src doctor
if ($LASTEXITCODE -ne 0) { throw "Environment inspection failed." }
