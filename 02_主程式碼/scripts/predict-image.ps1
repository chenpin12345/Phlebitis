param([string]$ImagePath = "", [string]$Device = "0")
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $projectRoot
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
# Data lives in the workspace's 03_* folder (see workspace-layout.json); older single-folder layout falls back to the code folder.
$storeDir = Get-ChildItem -LiteralPath (Join-Path $projectRoot "..") -Directory -Filter "03_*" -ErrorAction SilentlyContinue | Select-Object -First 1
$storeRoot = if ($storeDir) { $storeDir.FullName } else { $projectRoot }
if (-not (Test-Path -LiteralPath $pythonExe)) { throw "請先執行 scripts\setup.ps1 建立環境。" }
if (-not (Test-Path -LiteralPath (Join-Path $storeRoot "models\selected\best.pt"))) { throw "請先完成訓練及 select 模型。" }
if (-not $ImagePath) {
    Add-Type -AssemblyName System.Windows.Forms
    $picker = New-Object System.Windows.Forms.OpenFileDialog
    $picker.Title = "選擇要分析的照片"
    $picker.Filter = "照片 (*.jpg;*.jpeg;*.png;*.webp)|*.jpg;*.jpeg;*.png;*.webp"
    $picker.InitialDirectory = Join-Path $storeRoot "data\approved\images"
    try {
        if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit 0 }
        $ImagePath = $picker.FileName
    }
    finally { $picker.Dispose() }
}
Write-Host "本地研究展示：輸出疑似區域，不提供嚴重度分級。"
& $pythonExe -m src predict $ImagePath --device $Device --allow-demo
if ($LASTEXITCODE -ne 0) { throw "分析失敗，請查看上方訊息。" }
$latestResult = Get-ChildItem -LiteralPath (Join-Path $storeRoot "runs") -Directory |
    Where-Object { $_.Name -like "prediction_*" } |
    Sort-Object Name -Descending |
    Select-Object -First 1
if ($latestResult) { Invoke-Item -LiteralPath $latestResult.FullName }
