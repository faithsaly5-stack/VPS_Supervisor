@echo off
echo =======================================================
echo          Elite Administration Console Launcher
echo =======================================================
echo.
echo Starting Web Dashboard...
echo.

powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0start.ps1"

echo.
echo Server stopped.
pause
