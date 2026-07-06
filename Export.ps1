$source = "$PSScriptRoot\*"
$destination = "$env:USERPROFILE\Desktop\VPS_Supervisor_Source.zip"

Write-Host "======================================================="
Write-Host "         Master VPS Supervisor - Release Packager"
Write-Host "======================================================="
Write-Host ""

if (Test-Path $destination) {
    Remove-Item $destination -Force
}

Write-Host "Stripping personal credentials (.env, memory files)..."
Write-Host "Excluding heavy virtual environments (venv)..."
Write-Host ""
Write-Host "Zipping project..."

Get-ChildItem -Path $PSScriptRoot -Exclude ".env", ".ai_memory.json", ".ai_long_memory.txt", "venv", "__pycache__", ".git", "*.zip", ".agents" | Compress-Archive -DestinationPath $destination -Force

Write-Host ""
Write-Host "[SUCCESS] Your clean project has been securely zipped!"
Write-Host "You can find 'VPS_Supervisor_Source.zip' directly on your Desktop."
Write-Host ""
