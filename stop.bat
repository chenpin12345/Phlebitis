@echo off
rem Stop this project's workbench (8765) and LINE service (8000). Other programs are not touched.
setlocal
set "CODE="
for /d %%D in ("%~dp002_*") do set "CODE=%%~fD"
if not defined CODE (
  echo Code folder 02_* was not found next to this file.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CODE%\scripts\stop-services.ps1"
pause
