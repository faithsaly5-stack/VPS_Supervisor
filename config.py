import os
import click
import getpass
from rich.console import Console
from cryptography.fernet import Fernet

console = Console()

def get_fernet():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(script_dir, ".secret.key")
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, "wb") as f:
            f.write(key)
    else:
        with open(key_path, "rb") as f:
            key = f.read()
    return Fernet(key)

def save_config(config):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    lines = []
    for k, v in config.items():
        if v is not None:
            lines.append(f"{k}={v}")
    raw_data = "\n".join(lines).encode("utf-8")
    
    fernet = get_fernet()
    encrypted_data = fernet.encrypt(raw_data)
    
    with open(env_path, "wb") as f:
        f.write(encrypted_data)

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
        try:
            with open(env_path, "rb") as f:
                data = f.read()
            fernet = get_fernet()
            try:
                decrypted = fernet.decrypt(data).decode("utf-8")
            except Exception:
                # Fallback if the file was not encrypted (migration)
                decrypted = data.decode("utf-8-sig")
                
            for line in decrypted.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    config[key] = val
                    
            # Migrate to encrypted if it wasn't
            try:
                fernet.decrypt(data)
            except Exception:
                save_config(config)
                
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
                        
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
            
        save_config(config)
        console.print("[green]Configuration saved securely to .env[/green]")
        
    return config
