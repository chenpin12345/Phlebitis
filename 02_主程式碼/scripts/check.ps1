# One command to run before every commit: formatting, automated tests and the web build.
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check.ps1
# Add -Fix to apply the formatting first instead of only checking it.
param([switch]$Fix)
$ErrorActionPreference = 'Stop'
$code = Split-Path -Parent $PSScriptRoot
$python = Join-Path $code '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw '尚未安裝環境：請先執行根目錄的 setup.bat。' }
Push-Location -LiteralPath $code
try {
    Write-Host '1/4 Python 排版（black）'
    if ($Fix) { & $python -m black src tests scripts } else { & $python -m black --check --quiet src tests scripts }
    if ($LASTEXITCODE -ne 0) { throw 'Python 排版不符：執行 scripts\check.ps1 -Fix 後再檢查。' }

    Write-Host '2/4 網頁排版（prettier）'
    Push-Location -LiteralPath (Join-Path $code 'web')
    try {
        if ($Fix) { npx prettier --write 'src/**/*.{ts,tsx}' '*.mjs' vite.config.ts } else { npx prettier --check 'src/**/*.{ts,tsx}' '*.mjs' vite.config.ts }
        if ($LASTEXITCODE -ne 0) { throw '網頁排版不符：執行 scripts\check.ps1 -Fix 後再檢查。' }
    } finally { Pop-Location }

    Write-Host '3/4 自動測試（pytest，約 3 分鐘）'
    & $python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw '自動測試失敗，請查看上方訊息。' }

    Write-Host '4/4 網頁建置（npm run build）'
    Push-Location -LiteralPath (Join-Path $code 'web')
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) { throw '網頁建置失敗，請查看上方訊息。' }
    } finally { Pop-Location }

    Write-Host '全部通過。' -ForegroundColor Green
} finally { Pop-Location }
