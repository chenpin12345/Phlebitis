@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0scripts\predict-image.ps1"
pause
