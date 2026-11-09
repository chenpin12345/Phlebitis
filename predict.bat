@echo off
rem Analyse one photo with the selected local model (opens a file picker; results open in a folder).
rem ASCII only on purpose: the code folder is located by its "02_" prefix.
setlocal
set "CODE="
for /d %%D in ("%~dp002_*") do set "CODE=%%~fD"
if not defined CODE (
  echo Code folder 02_* was not found next to this file.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%CODE%\scripts\predict-image.ps1"
pause
