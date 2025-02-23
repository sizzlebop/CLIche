"""
Process management commands
"""
import click
import psutil
import os
import signal
from typing import Optional

def get_process_name(pid: int) -> Optional[str]:
    """Get process name for a given PID."""
    try:
        process = psutil.Process(pid)
        return process.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

@click.command()
@click.argument('pid', type=int)
def kill(pid: int):
    """Kill a process by PID"""
    try:
        process = psutil.Process(pid)
        process_name = process.name()
        
        # Try SIGTERM first
        process.terminate()
        
        try:
            process.wait(timeout=3)
            click.echo(f"Process {pid} ({process_name}) terminated successfully")
        except psutil.TimeoutExpired:
            # If SIGTERM didn't work, try SIGKILL
            process.kill()
            click.echo(f"Process {pid} ({process_name}) killed forcefully")
            
    except psutil.NoSuchProcess:
        click.echo(f"No process found with PID {pid}")
    except psutil.AccessDenied:
        click.echo(f"Permission denied to kill process {pid}")
    except Exception as e:
        click.echo(f"Error killing process {pid}: {str(e)}")
