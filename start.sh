#!/bin/bash

# Master VPS Supervisor - Linux Launcher

# Force UTF-8 encoding
export PYTHONIOENCODING=utf-8

clear

cat << "EOF"
 _    ______  _____    _____ __  ______  __________ _    ___________ ____  ____ 
| |  / / __ \/ ___/   / ___// / / / __ \/ ____/ __ \ |  / /  _/ ___// __ \/ __ \
| | / / /_/ /\__ \    \__ \/ / / / /_/ / __/ / /_/ / | / // / \__ \/ / / / /_/ /
| |/ / ____/___/ /   ___/ / /_/ / ____/ /___/ _, _/| |/ // / ___/ / /_/ / _, _/ 
|___/_/    /____/   /____/\____/_/   /_____/_/ |_| |___/___//____/\____/_/ |_|  
EOF

echo -e "\e[36m=======================================================\e[0m"
echo -e "\e[97m          Elite Administration Console Activated       \e[0m"
echo -e "\e[36m=======================================================\e[0m"
echo ""

# Configuration check
if [ ! -f ".env" ]; then
    echo -e "\e[33m\n[!] Configuration file (.env) not found. Starting Initial Setup...\e[0m"
    
    read -p "Enter VPS IP Address: " inputIp
    read -p "Enter VPS Username (press Enter for 'root'): " inputUser
    inputUser=${inputUser:-root}
    
    read -s -p "Enter VPS Password: " inputPass
    echo ""
    read -p "Enter Gemini API Key(s) [comma separated]: " inputKeys
    
    echo -e "VPS_IP=$inputIp\nVPS_USER=$inputUser\nVPS_PASS=$inputPass\nGEMINI_API_KEYS=$inputKeys" > .env
    echo -e "\e[32m[OK] Configuration saved securely to .env\e[0m"
    vpsIp=$inputIp
else
    vpsIp=$(grep "^VPS_IP=" .env | cut -d '=' -f2)
fi

echo -e "\e[90m[System] Performing Pre-flight checks...\e[0m"
echo -ne "\e[90m   -> Pinging VPS ($vpsIp)... \e[0m"

if ping -c 1 -W 2 "$vpsIp" &> /dev/null; then
    echo -e "\e[32m[ONLINE]\e[0m"
else
    echo -e "\e[31m[UNREACHABLE]\e[0m"
    echo -e "\e[33m[!] Warning: The VPS seems unreachable. Commands may fail.\e[0m"
fi

# Check for virtual environment
if [ ! -f "venv/bin/activate" ]; then
    echo -e "\e[33m\n[System] Virtual environment missing. Creating now...\e[0m"
    if ! command -v python3 &> /dev/null; then
        echo -e "\e[31m[!] python3 is required but not installed.\e[0m"
        exit 1
    fi
    
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "\e[31m[!] Failed to create virtual environment.\e[0m"
        echo -e "\e[33mIf you are on Debian/Ubuntu, you are likely missing the python3-venv dependency.\e[0m"
        echo -e "\e[33mPlease run: sudo apt install python3-venv\e[0m"
        exit 1
    fi
fi

# Activate venv
echo -ne "\e[90m   -> Activating Python environment... \e[0m"
source venv/bin/activate
echo -e "\e[32m[OK]\e[0m"

# Install dependencies silently
echo -ne "\e[90m   -> Verifying core dependencies... \e[0m"
pip install -r requirements.txt -q
echo -e "\e[32m[OK]\e[0m"

sleep 1
clear

cat << "EOF"
 _    ______  _____    _____ __  ______  __________ _    ___________ ____  ____ 
| |  / / __ \/ ___/   / ___// / / / __ \/ ____/ __ \ |  / /  _/ ___// __ \/ __ \
| | / / /_/ /\__ \    \__ \/ / / / /_/ / __/ / /_/ / | / // / \__ \/ / / / /_/ /
| |/ / ____/___/ /   ___/ / /_/ / ____/ /___/ _, _/| |/ // / ___/ / /_/ / _, _/ 
|___/_/    /____/   /____/\____/_/   /_____/_/ |_| |___/___//____/\____/_/ |_|  
EOF
echo -e "\e[36m=======================================================\e[0m"
echo -e "\e[97m          Elite Administration Console Activated       \e[0m"
echo -e "\e[36m=======================================================\e[0m"
echo ""
echo -e "\e[32m[OK] Core Systems Online and Ready.\e[0m"
echo -e "\e[90m[i] Launching Web Dashboard...\e[0m"
echo -e "\e[36m=======================================================\e[0m"
echo ""

# Start Flask Server
python3 server.py
