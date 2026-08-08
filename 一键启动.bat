@echo off
setlocal
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0start-all.ps1"
if errorlevel 1 (
  echo.
  echo Start failed. Please check the error above.
  pause
)
