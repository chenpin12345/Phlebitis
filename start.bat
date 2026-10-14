@echo off
rem Start the Phlebitis research workbench (http://127.0.0.1:8765).
rem ASCII only on purpose: the code folder is located by its "02_" prefix.
setlocal
set "CODE="
for /d %%D in ("%~dp002_*") do set "CODE=%%~fD"
if not defined CODE (
  echo Code folder 02_* was not found next to this file.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CODE%\scripts\start-workbench.ps1"
pause
