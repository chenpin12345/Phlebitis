$ErrorActionPreference = 'Stop'
Write-Host '正在啟動研究工作台…'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw '尚未安裝環境：請先執行根目錄的 setup.bat。' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'web\dist\index.html'))) { throw '網頁尚未建置：請先執行根目錄的 setup.bat。' }
# Fast presence check (about 0.1 s). Importing torch here took 9+ s on every start;
# deep compatibility checks belong to setup.bat, and training reports real import errors itself.
& $pythonPath -c "import importlib.util as u, sys; missing=[m for m in ('fastapi','uvicorn','torch','torchvision','cv2','transformers','safetensors','sklearn','psutil') if u.find_spec(m) is None]; print('缺少套件：'+', '.join(missing)) if missing else None; sys.exit(1 if missing else 0)"
if ($LASTEXITCODE -ne 0) { throw '缺少必要套件：請執行根目錄的 setup.bat 後再試。' }
$occupied = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if ($occupied) {
    Write-Host '工作台已在執行，請開啟 http://127.0.0.1:8765'
    Start-Process 'http://127.0.0.1:8765'
    return
}
# Open the browser as soon as the server accepts connections (gives up after 60 s).
$null = Start-Job -ScriptBlock {
    for ($i = 0; $i -lt 120; $i++) {
        try { $client = New-Object System.Net.Sockets.TcpClient; $client.Connect('127.0.0.1', 8765); $client.Close(); Start-Process 'http://127.0.0.1:8765'; return }
        catch { Start-Sleep -Milliseconds 500 }
    }
}
Write-Host '研究工作台：http://127.0.0.1:8765（就緒後會自動開啟瀏覽器）'
Write-Host '請保持此視窗開啟；按 Ctrl+C 或執行 stop.bat 可停止。'
& $pythonPath -m src workbench --port 8765
if ($LASTEXITCODE -ne 0) { throw '工作台因錯誤停止，請查看上方訊息。' }
