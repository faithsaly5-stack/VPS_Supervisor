import warnings
# Suppress Paramiko's TripleDES deprecation warning to keep CLI output clean
warnings.filterwarnings("ignore", category=UserWarning, module='paramiko')
warnings.filterwarnings("ignore", category=DeprecationWarning)

import paramiko
import getpass
import sys
import os
import time
import threading
from rich.console import Console

console = Console()

class SSHClient:
    def __init__(self, hostname, username, port=22):
        self.hostname = hostname
        self.username = username
        self.port = port
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._connected = False

    def connect(self, password=None):
        if self._connected:
            return
        
        try:
            # First, try connecting with local SSH keys
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=password,
                timeout=30,
                banner_timeout=30
            )
            self._connected = True
        except paramiko.AuthenticationException:
            if password is not None:
                console.print("[bold red]Authentication failed with provided credentials.[/bold red]")
                return
            
            # If no password provided and keys failed, prompt for a transient password
            console.print("[yellow]SSH key authentication failed or unavailable. Please provide password.[/yellow]")
            transient_password = getpass.getpass(f"Password for {self.username}@{self.hostname}: ")
            try:
                self.client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    password=transient_password,
                    timeout=30,
                    banner_timeout=30
                )
                self._connected = True
            except paramiko.AuthenticationException:
                console.print("[bold red]Authentication failed. Terminating operation.[/bold red]")
                exit(1)
        except Exception as e:
            console.print(f"[bold red]Connection error: {e}[/bold red]")
            exit(1)

    def execute_command(self, command, require_sudo=False, interactive=False):
        if not self._connected:
            self.connect()

        if interactive:
            try:
                channel = self.client.get_transport().open_session()
                channel.get_pty()
                channel.exec_command(command)

                output_buffer = []

                def receive_output():
                    while not channel.exit_status_ready() or channel.recv_ready():
                        if channel.recv_ready():
                            data = channel.recv(4096)
                            if data:
                                decoded = data.decode('utf-8', errors='replace')
                                sys.stdout.write(decoded)
                                sys.stdout.flush()
                                output_buffer.append(decoded)
                        else:
                            time.sleep(0.01)
                            
                recv_thread = threading.Thread(target=receive_output)
                recv_thread.daemon = True
                recv_thread.start()

                is_windows = os.name == 'nt'
                if is_windows:
                    import msvcrt

                while not channel.exit_status_ready():
                    if is_windows and sys.stdin.isatty():
                        if msvcrt.kbhit():
                            ch = msvcrt.getch()
                            if ch == b'\r':
                                ch = b'\n'
                            channel.send(ch)
                        else:
                            time.sleep(0.01)
                    else:
                        time.sleep(0.01)

                recv_thread.join(timeout=1.0)
                exit_status = channel.recv_exit_status()
                out = "".join(output_buffer)
                
                return exit_status, out, ""
            except Exception as e:
                console.print(f"[bold red]Interactive execution error: {e}[/bold red]")
                return -1, "", str(e)
        else:
            try:
                stdin, stdout, stderr = self.client.exec_command(command)
                exit_status = stdout.channel.recv_exit_status()
                
                out = stdout.read().decode('utf-8').strip()
                err = stderr.read().decode('utf-8').strip()

                return exit_status, out, err
            except Exception as e:
                console.print(f"[bold red]Execution error: {e}[/bold red]")
                return -1, "", str(e)

    def close(self):
        if self._connected:
            self.client.close()
            self._connected = False
