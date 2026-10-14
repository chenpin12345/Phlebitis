@echo off
rem Install or repair the Python environment and build the web UI. Does not touch data.
setlocal
set "CODE="
for /d %%D in ("%~dp002_*") do set "CODE=%%~fD"
if not defined CODE (
  echo Code folder 02_* was not found next to this file.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CODE%\scripts\setup-workbench.ps1"
pause
