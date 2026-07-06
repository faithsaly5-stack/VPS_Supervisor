import os
import click
import getpass
from rich.console import Console

console = Console()

def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    
    config = {
        "VPS_IP": None,
        "VPS_USER": None,
        "VPS_PASS": None,
        "GEMINI_API_KEYS": None
    }
    
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    config[key] = val
                        
    # Check if any required keys are missing
    missing = [k for k in config if not config[k]]
    if missing:
        console.print("[yellow]Configuration missing or incomplete. Starting Setup Wizard...[/yellow]")
        
        if not config["VPS_IP"]:
            config["VPS_IP"] = click.prompt("Enter VPS IP Address")
        if not config["VPS_USER"]:
            config["VPS_USER"] = click.prompt("Enter VPS Username", default="root")
        if not config["VPS_PASS"]:
            config["VPS_PASS"] = getpass.getpass("Enter VPS Password: ")
        if not config["GEMINI_API_KEYS"]:
            config["GEMINI_API_KEYS"] = click.prompt("Enter Gemini API Key(s) [comma separated]")
            
        with open(env_path, "w") as f:
            for k, v in config.items():
                f.write(f"{k}={v}\n")
                
        console.print("[green]Configuration saved securely to .env[/green]")
        
    return config
