import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ssh_client import SSHClient
import re
import os
import random
import json

console = Console()

from config import load_config

def get_ssh_client():
    config = load_config()
    ip = config.get("VPS_IP")
    user = config.get("VPS_USER")
    password = config.get("VPS_PASS")
    
    if not ip or not user:
        console.print("[red]Critical configuration missing. Please check your .env file.[/red]")
        exit(1)

    client = SSHClient(hostname=ip, username=user)
    client.connect(password=password)
    return client


def load_memory():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mem_path = os.path.join(script_dir, ".ai_memory.json")
    if os.path.exists(mem_path):
        try:
            with open(mem_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_memory(memory):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mem_path = os.path.join(script_dir, ".ai_memory.json")
    with open(mem_path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)

def load_long_memory():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lm_path = os.path.join(script_dir, ".ai_long_memory.txt")
    if os.path.exists(lm_path):
        with open(lm_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "No long-term memory yet."

def save_long_memory(text):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lm_path = os.path.join(script_dir, ".ai_long_memory.txt")
    with open(lm_path, "w", encoding="utf-8") as f:
        f.write(text)

@click.group()
def cli():
    """Master VPS Supervisor - Elite Administration CLI"""
    pass

@cli.command()
def monitor():
    """Monitor core routing daemons (xray, v2ray, 3x-ui)."""
    client = get_ssh_client()
    services = ['xray', 'v2ray', '3x-ui']
    
    table = Table(title="Core Services Status")
    table.add_column("Service", style="cyan", no_wrap=True)
    table.add_column("Status", justify="left", style="magenta")
    
    for svc in services:
        status_cmd = f"systemctl is-active {svc}"
        exit_code, out, err = client.execute_command(status_cmd)
        
        if exit_code == 0:
            status_text = "[green]Active (Running)[/green]"
        else:
            status_text = f"[red]Inactive or Failed ({out})[/red]"
            
        table.add_row(svc, status_text)
        
    console.print(table)
    client.close()

@cli.command()
def traffic():
    """Audit network traffic and bandwidth using vnstat."""
    client = get_ssh_client()
    exit_code, out, err = client.execute_command("vnstat -i eth0") # Assumes eth0, vnstat will default to main interface if not provided, let's just use vnstat
    if exit_code != 0:
        exit_code, out, err = client.execute_command("vnstat")
        if exit_code != 0:
            console.print("[red]vnstat may not be installed or configured.[/red]")
            client.close()
            return
            
    console.print(Panel(out, title="Bandwidth Auditing (vnstat)", border_style="cyan"))
    client.close()

@cli.command()
def resources():
    """Monitor CPU load, RAM allocation, and disk space."""
    client = get_ssh_client()
    
    # RAM
    code, ram_out, err = client.execute_command("free -h")
    # Disk
    code, disk_out, err = client.execute_command("df -h /")
    # CPU
    code, cpu_out, err = client.execute_command("top -b -n 1 | head -n 5")
    
    console.print(Panel(ram_out, title="RAM Allocation", border_style="blue"))
    console.print(Panel(disk_out, title="Disk Space", border_style="yellow"))
    console.print(Panel(cpu_out, title="CPU Load", border_style="magenta"))
    
    client.close()

@cli.command()
@click.option('--lines', default=50, help='Number of log lines to fetch.')
@click.option('--log', type=click.Choice(['syslog', 'auth', 'xray', '3x-ui']), default='syslog', help='Log file to analyze.')
def logs(lines, log):
    """Analyze and triage system logs."""
    client = get_ssh_client()
    
    log_commands = {
        'syslog': f"tail -n {lines} /var/log/syslog",
        'auth': f"tail -n {lines} /var/log/auth.log",
        'xray': f"journalctl -u xray --no-pager -n {lines}",
        '3x-ui': f"journalctl -u x-ui --no-pager -n {lines}"
    }
    
    cmd = log_commands[log]
    
    console.print(f"[cyan]Fetching last {lines} lines for {log}...[/cyan]")
    code, out, err = client.execute_command(cmd)
    
    if code != 0:
        console.print(f"[red]Error fetching log: {err}[/red]")
        client.close()
        return

    # Basic triage/filtering for errors
    errors_found = False
    for line in out.splitlines():
        if re.search(r'(error|failed|fatal|critical|denied|disconnect)', line, re.IGNORECASE):
            console.print(f"[red]{line}[/red]")
            errors_found = True
            
    if not errors_found:
        console.print("[green]No obvious errors found in the filtered log segment.[/green]")
    else:
        console.print("[yellow]Review highlighted lines. Consider restarting relevant services if issues persist.[/yellow]")

    client.close()

@cli.command()
@click.argument('command_string', nargs=-1)
def execute(command_string):
    """Safely execute custom commands on the VPS."""
    if not command_string:
        console.print("[red]No command provided.[/red]")
        return
        
    cmd = " ".join(command_string)
    
    # Destructive or altering command safety check
    dangerous_patterns = ['ufw', 'iptables', 'rm', 'ip route', 'reboot', 'shutdown', 'systemctl stop', 'systemctl disable']
    
    is_dangerous = any(pat in cmd for pat in dangerous_patterns)
    
    if is_dangerous:
        console.print(f"[bold red]WARNING: The requested command modifies network routes, firewall rules, or performs destructive actions.[/bold red]")
        console.print(f"Command to be executed: [bold yellow]{cmd}[/bold yellow]")
        if not click.confirm("Do you explicitly authorize this command to proceed?"):
            console.print("[green]Execution aborted by operator.[/green]")
            return
            
    client = get_ssh_client()
    console.print(f"[cyan]Executing: {cmd}[/cyan]")
    code, out, err = client.execute_command(cmd, interactive=True)
    
    if err:
        console.print(f"[red]{err}[/red]")
        
    client.close()

@cli.command()
@click.argument('prompt_words', nargs=-1)
def ai(prompt_words):
    """Use Gemini AI to manage the VPS based on natural language."""
    if not prompt_words:
        console.print("[red]No prompt provided.[/red]")
        return
        
    user_input = " ".join(prompt_words)
    
    config = load_config()
    content_keys = config.get("GEMINI_API_KEYS")
    if not content_keys:
        console.print("[red]Error: No API keys found in configuration.[/red]")
        return
        
    api_keys = [k.strip() for k in content_keys.split(",") if k.strip()]
    if not api_keys:
        console.print("[red]Error: No valid API keys found in configuration.[/red]")
        return
        
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        console.print("[red]Error: google-genai is not installed. Please install it first.[/red]")
        return
        
    model = "gemini-3.1-flash-lite"
    
    long_memory_text = load_long_memory()
    
    system_instruction = f"You are a Linux VPS administrator. The user will ask you to perform a task on their server. Provide the exact bash command to execute to fulfill their request. ALWAYS prioritize non-interactive commands (e.g., use DEBIAN_FRONTEND=noninteractive, -y flags, or pipe 'yes' to commands) to ensure smooth automation. If a command absolutely MUST be interactive, it is permitted. DO NOT provide any explanation, markdown formatting, or markdown code blocks. Output ONLY the raw command. If the user speaks Farsi, you MUST respond, summarize, and explain completely in Farsi.\n\n### LONG-TERM KNOWLEDGE BASE ###\n{long_memory_text}"
    
    memory = load_memory()
    
    contents = []
    for msg in memory:
        contents.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["text"])]
            )
        )
        
    new_user_msg = f"User Request: {user_input}"
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=new_user_msg)]
        )
    )
    
    # Inject system instruction into the very first message
    if contents:
        contents[0].parts[0].text = f"System Instruction: {system_instruction}\\n\\n" + contents[0].parts[0].text
        
    generate_content_config = types.GenerateContentConfig()
    console.print("[cyan]Consulting Gemini 3.1 Flash-Lite...[/cyan]")
    
    success = False
    random.shuffle(api_keys)
    active_client = None
    command_to_run = ""
    
    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            command_to_run = ""
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if text := chunk.text:
                    command_to_run += text
            success = True
            active_client = client
            break
        except Exception:
            continue
            
    if not success:
        console.print("[red]API Error: All API keys failed or were rate-limited.[/red]")
        return
        
    command_to_run = command_to_run.strip()
    
    if command_to_run.startswith("```bash"):
        command_to_run = command_to_run[7:]
    if command_to_run.startswith("```"):
        command_to_run = command_to_run[3:]
    if command_to_run.endswith("```"):
        command_to_run = command_to_run[:-3]
    command_to_run = command_to_run.strip()
    
    console.print(f"Gemini suggests executing: [bold yellow]{command_to_run}[/bold yellow]")
    if not click.confirm("Do you explicitly authorize this command to proceed?"):
        console.print("[green]Execution aborted by operator.[/green]")
        return
        
    ssh_client = get_ssh_client()
    console.print(f"[cyan]Executing: {command_to_run}[/cyan]")
    code, out, err = ssh_client.execute_command(command_to_run, interactive=True)
    
    if err:
        console.print(f"[red]{err}[/red]")
        
    ssh_client.close()

    console.print("[cyan]Asking Gemini to verify the output...[/cyan]")
    verify_instruction = "You are a Linux VPS administrator. The user executed a command you suggested. Analyze the exit code, stdout, and stderr. Provide a short, natural language summary of whether the command succeeded and what the result means."
    verify_input = f"Command Executed: {command_to_run}\\nExit Code: {code}\\nStdout: {out}\\nStderr: {err}"
    
    # We must append the model's generated command, then the user's execution result
    memory.append({"role": "user", "text": new_user_msg})
    memory.append({"role": "model", "text": command_to_run})
    memory.append({"role": "user", "text": f"Execution Result: {verify_input}"})
    
    verify_contents = []
    for msg in memory:
        verify_contents.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["text"])]
            )
        )
        
    if verify_contents:
        verify_contents[0].parts[0].text = f"System Instruction: {verify_instruction}\\n\\n" + verify_contents[0].parts[0].text
    
    verify_output = ""
    try:
        for chunk in active_client.models.generate_content_stream(
            model=model,
            contents=verify_contents,
            config=generate_content_config,
        ):
            if text := chunk.text:
                verify_output += text
        console.print(Panel(verify_output.strip(), title="AI Verification", border_style="magenta"))
        
        # Save verification output to memory
        memory.append({"role": "model", "text": verify_output.strip()})
        save_memory(memory)
        
    except Exception as e:
        console.print(f"[yellow]Could not verify output with AI: {e}[/yellow]")
        save_memory(memory)

    if len(memory) >= 80:
        console.print("[cyan]Short-term memory limit reached. Compacting oldest conversations into long-term memory...[/cyan]")
        messages_to_compact = memory[:20]
        
        compaction_instruction = "You are a highly intelligent memory manager. You will be provided with the current LONG-TERM KNOWLEDGE BASE and a recent SHORT-TERM CONVERSATION. Your task is to extract any new, important, and persistent facts (like installed software, user preferences, configurations, architecture details) from the short-term conversation. Update the long-term knowledge base. DO NOT duplicate existing facts. Ignore transient or unimportant details. Output ONLY the updated long-term knowledge base as a clean, concise bulleted list."
        
        compaction_prompt = f"### CURRENT LONG-TERM KNOWLEDGE BASE ###\n{long_memory_text}\n\n### RECENT SHORT-TERM CONVERSATION ###\n" + json.dumps(messages_to_compact, indent=2)
        
        comp_contents = [
            types.Content(role="user", parts=[types.Part.from_text(text=compaction_instruction + "\n\n" + compaction_prompt)])
        ]
        
        new_long_memory = ""
        try:
            for chunk in active_client.models.generate_content_stream(
                model=model,
                contents=comp_contents,
                config=generate_content_config,
            ):
                if text := chunk.text:
                    new_long_memory += text
            
            new_long_memory = new_long_memory.strip()
            if new_long_memory:
                if new_long_memory.startswith("```"):
                    new_long_memory = new_long_memory.split("\n", 1)[-1]
                if new_long_memory.endswith("```"):
                    new_long_memory = new_long_memory.rsplit("\n", 1)[0]
                    
                save_long_memory(new_long_memory.strip())
                console.print("[green]Long-term memory successfully updated.[/green]")
                
                memory = memory[20:]
                save_memory(memory)
        except Exception as e:
            console.print(f"[yellow]Could not compact memory: {e}[/yellow]")

@cli.command(name='ai-clear')
def ai_clear():
    """Clear the AI's conversation memory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mem_path = os.path.join(script_dir, ".ai_memory.json")
    if os.path.exists(mem_path):
        os.remove(mem_path)
        console.print("[green]AI memory cleared successfully.[/green]")
    else:
        console.print("[yellow]AI memory is already empty.[/yellow]")

if __name__ == '__main__':
    cli()
