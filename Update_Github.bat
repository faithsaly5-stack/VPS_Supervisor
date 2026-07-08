@echo off
echo ==========================================
echo        Push Updates to GitHub
echo ==========================================
echo.

:: --- SAFETY ENFORCEMENT ---
:: Ensure sensitive files are forcefully untracked and unstaged
:: just in case they were accidentally added before .gitignore was configured.
git rm -r --cached .env .ai_memory.json .ai_long_memory.txt venv __pycache__ .agents >nul 2>&1

set /p commitMsg="Enter update message (or press Enter for 'Auto-update'): "
if "%commitMsg%"=="" set commitMsg=Auto-update

echo.
echo Adding files to Git...
git add .

:: Secondary safety check: Unstage sensitive files before commit just in case
git reset HEAD .env .ai_memory.json .ai_long_memory.txt venv __pycache__ .agents >nul 2>&1

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
