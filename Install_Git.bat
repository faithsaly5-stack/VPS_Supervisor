@echo off
echo =======================================================
echo              Git Auto-Installer
echo =======================================================
echo.
echo Downloading and installing Git...
echo Please click "Yes" if a Windows Security prompt appears!
echo.

winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements

echo.
echo =======================================================
echo Installation Complete! 
echo VERY IMPORTANT: You must restart any open terminal windows
echo or Visual Studio Code so Windows can detect the 'git' command.
echo =======================================================
pause
