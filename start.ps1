$Host.UI.RawUI.WindowTitle = "Master VPS Supervisor - Pro Edition"

# Force UTF-8 encoding for Farsi support
[console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 > $null

Clear-Host

$asciiArt = @"
 _    ______  _____    _____ __  ______  __________ _    ___________ ____  ____ 
| |  / / __ \/ ___/   / ___// / / / __ \/ ____/ __ \ |  / /  _/ ___// __ \/ __ \
| | / / /_/ /\__ \    \__ \/ / / / /_/ / __/ / /_/ / | / // / \__ \/ / / / /_/ /
| |/ / ____/___/ /   ___/ / /_/ / ____/ /___/ _, _/| |/ // / ___/ / /_/ / _, _/ 
|___/_/    /____/   /____/\____/_/   /_____/_/ |_| |___/___//____/\____/_/ |_| 
"@

Write-Host $asciiArt -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor DarkCyan
Write-Host "          Elite Administration Console Activated       " -ForegroundColor White
Write-Host "=======================================================" -ForegroundColor DarkCyan
Write-Host ""

$vpsIp = "Unknown"
if (-Not (Test-Path ".env")) {
    Write-Host "`n[!] Configuration file (.env) not found. Starting Initial Setup..." -ForegroundColor Yellow
    
    $inputIp = Read-Host "Enter VPS IP Address"
    $inputUser = Read-Host "Enter VPS Username (press Enter for 'root')"
    if ([string]::IsNullOrWhiteSpace($inputUser)) { $inputUser = "root" }
    
    $inputPass = Read-Host "Enter VPS Password"
    $inputKeys = Read-Host "Enter Gemini API Key(s) [comma separated]"
    
    $envContent = "VPS_IP=$inputIp`nVPS_USER=$inputUser`nVPS_PASS=$inputPass`nGEMINI_API_KEYS=$inputKeys`n"
    Set-Content -Path ".env" -Value $envContent -Encoding UTF8
    Write-Host "[OK] Configuration saved securely to .env" -ForegroundColor Green
    $vpsIp = $inputIp
} else {
    $envContent = Get-Content ".env"
    foreach ($line in $envContent) {
        if ($line -match "^VPS_IP=(.*)") {
            $vpsIp = $matches[1]
            break
        }
    }
}

# System Health Check
Write-Host "[System] Performing Pre-flight checks..." -ForegroundColor DarkGray
Write-Host "   -> Pinging VPS ($vpsIp)... " -NoNewline -ForegroundColor DarkGray
if (Test-Connection -ComputerName $vpsIp -Count 1 -Quiet -ErrorAction SilentlyContinue) {
    Write-Host "[ONLINE]" -ForegroundColor Green
} else {
    Write-Host "[UNREACHABLE]" -ForegroundColor Red
    Write-Host "[!] Warning: The VPS seems unreachable. Commands may fail." -ForegroundColor Yellow
}

# Check for virtual environment
if (-Not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "`n[System] Virtual environment missing. Creating now..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv by dot-sourcing
Write-Host "   -> Activating Python environment... " -NoNewline -ForegroundColor DarkGray
. ".\venv\Scripts\Activate.ps1"
Write-Host "[OK]" -ForegroundColor Green

# Install dependencies silently
Write-Host "   -> Verifying core dependencies... " -NoNewline -ForegroundColor DarkGray
pip install -r requirements.txt -q
Write-Host "[OK]" -ForegroundColor Green

Start-Sleep -Seconds 1
Clear-Host

Write-Host $asciiArt -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor DarkCyan
Write-Host "          Elite Administration Console Activated       " -ForegroundColor White
Write-Host "=======================================================" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "[OK] Core Systems Online and Ready." -ForegroundColor Green
Write-Host "[i] Launching Web Dashboard..." -ForegroundColor DarkGray
Write-Host "=======================================================" -ForegroundColor DarkCyan
Write-Host ""

# Launch browser
Start-Process "http://localhost:5000"

# Start Flask Server
python server.py
