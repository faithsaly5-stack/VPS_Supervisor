import sys
from ssh_client import SSHClient

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_cmd.py <command>")
        return

    command = " ".join(sys.argv[1:])
    
    from config import load_config
    config = load_config()
    
    password = config.get("VPS_PASS")
    if not password:
        print("Error: Password not found in .env")
        return

    client = SSHClient(hostname=config.get("VPS_IP"), username=config.get("VPS_USER"))
    
    client.connect(password=password)
    code, out, err = client.execute_command(command)
    
    if out:
        print(out)
    if err:
        print(f"STDERR: {err}", file=sys.stderr)
        
    client.close()

if __name__ == "__main__":
    main()
