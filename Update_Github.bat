@echo off
echo ==========================================
echo        Push Updates to GitHub
echo ==========================================
echo.
set /p commitMsg="Enter update message (or press Enter for 'Auto-update'): "
if "%commitMsg%"=="" set commitMsg=Auto-update

echo.
echo Adding files to Git...
git add .

echo.
echo Committing with message: "%commitMsg%"...
git commit -m "%commitMsg%"

echo.
echo Pushing to GitHub...
git push

echo.
echo ==========================================
echo               FINISHED!
echo ==========================================
pause
