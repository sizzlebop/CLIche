"""
Server management commands
"""
import click
import psutil
import json
import socket
import shutil
from typing import Dict, List, Optional, Tuple
from ..utils.docker import get_docker_containers

def get_service_default_ports() -> Dict[str, int]:
    """Return a mapping of services to their default ports."""
    return {
        'http': 80,
        'https': 443,
        'ssh': 22,
        'ftp': 21,
        'sftp': 22,
        'postgresql': 5432,
        'mysql': 3306,
        'mongodb': 27017,
        'redis': 6379,
        'elasticsearch': 9200,
        'nginx': 80,
        'apache': 80,
        'nodejs': 3000,
        'django': 8000,
        'flask': 5000,
        'rails': 3000,
        'jupyter': 8888,
        'streamlit': 8501,
        'react': 3000,
        'vue': 8080,
        'angular': 4200,
        'vite': 5173,
        'webpack': 8080,
        'next': 3000,
        'nuxt': 3000,
        'python-http': 8000,
        'ollama': 11434,
        'tensorboard': 6006,
        'mlflow': 5000,
        'gradio': 7860,
        'ray': 8265,
        'generic-server': 8080,
        'dev-server': 8080,
        'unknown-server': 8080
    }

def is_port_available(port: int) -> bool:
    """Check if a port is likely being used by a service."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', port))
        sock.close()
        return True
    except socket.error:
        return False

def is_system_port(port: int) -> bool:
    """Check if a port is likely a system port we want to filter out."""
    return port < 1024 and port not in [80, 443]  # Allow HTTP/HTTPS ports

def is_system_process(name: str, cmdline: List[str]) -> bool:
    """Check if a process is likely a system service we want to filter out."""
    cmd_str = ' '.join(cmdline).lower()
    return any(x in cmd_str for x in [
        'blueman',
        'mintreport',
        'gnome',
        'kde',
        'xfce',
        'systemd',
        'dbus',
        'pulseaudio',
        'networkmanager',
        'windsurf',  # Filter out IDE processes
        'language_server',
        'utility'
    ])

def get_short_command(cmdline: List[str]) -> str:
    """Get a simplified version of the command."""
    return ' '.join(cmdline[:2]) if len(cmdline) > 2 else ' '.join(cmdline)

def detect_server_type(name: str, cmdline: List[str]) -> Optional[str]:
    """Detect the type of server based on process name and command line."""
    cmd_str = ' '.join(cmdline).lower()
    name = name.lower()
    
    # Web Servers
    if 'nginx' in name:
        return 'nginx'
    elif 'apache' in name or 'httpd' in name:
        return 'apache'
    elif 'python' in name and 'http.server' in cmd_str:
        return 'python-http'
        
    # Databases
    elif 'postgres' in name:
        return 'postgresql'
    elif 'mysql' in name:
        return 'mysql'
    elif 'mongodb' in name or 'mongod' in name:
        return 'mongodb'
    elif 'redis' in name or 'redis-server' in name:
        return 'redis'
    elif 'elasticsearch' in name:
        return 'elasticsearch'
        
    # AI/ML Servers
    elif 'ollama' in name or 'ollama' in cmd_str:
        return 'ollama'
    elif 'tensorboard' in cmd_str:
        return 'tensorboard'
    elif 'mlflow' in cmd_str:
        return 'mlflow'
    elif 'gradio' in cmd_str:
        return 'gradio'
    elif 'ray' in name or 'ray' in cmd_str:
        return 'ray'
        
    # Application Servers
    elif 'node' in name or 'npm' in cmd_str:
        if 'next' in cmd_str:
            return 'next'
        elif 'nuxt' in cmd_str:
            return 'nuxt'
        elif 'vite' in cmd_str:
            return 'vite'
        elif 'webpack' in cmd_str:
            return 'webpack'
        elif 'react' in cmd_str:
            return 'react'
        elif 'vue' in cmd_str:
            return 'vue'
        elif 'angular' in cmd_str or 'ng serve' in cmd_str:
            return 'angular'
        elif 'server.js' in cmd_str or 'app.js' in cmd_str:
            return 'nodejs'
            
    elif 'python' in name:
        if 'django' in cmd_str:
            return 'django'
        elif 'flask' in cmd_str:
            return 'flask'
        elif 'streamlit' in cmd_str:
            return 'streamlit'
        elif 'jupyter' in cmd_str:
            return 'jupyter'
            
    elif 'ruby' in name and ('rails' in cmd_str or 'puma' in cmd_str):
        return 'rails'
            
    return None

def get_all_servers() -> List[Dict]:
    """Get all running server processes regardless of open ports."""
    servers = []
    default_ports = get_service_default_ports()
    
    # First, let's get all processes listening on any port
    listening_processes = {}  # pid -> ports
    for conn in psutil.net_connections(kind='inet'):
        try:
            if conn.status == 'LISTEN' and not is_system_port(conn.laddr.port):
                if conn.pid not in listening_processes:
                    listening_processes[conn.pid] = set()
                listening_processes[conn.pid].add(conn.laddr.port)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Now get process details for all listening processes
    for pid, ports in listening_processes.items():
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            cmdline = proc.cmdline()
            if not cmdline or is_system_process(name, cmdline):
                continue
                
            server_type = detect_server_type(name, cmdline)
            if not server_type:
                # If we can't detect the type but it's listening, mark it as a generic server
                if any('server' in arg.lower() for arg in cmdline):
                    server_type = 'generic-server'
                elif any('dev' in arg.lower() for arg in cmdline):
                    server_type = 'dev-server'
                else:
                    server_type = 'unknown-server'
                    
            servers.append({
                'pid': pid,
                'name': name,
                'type': server_type,
                'ports': sorted(ports),
                'command': get_short_command(cmdline)
            })
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    # Also check for known server types that might not be listening yet
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            info = proc.info
            if not info['cmdline'] or info['pid'] in listening_processes or is_system_process(info['name'], info['cmdline']):
                continue
                
            name = info['name']
            cmdline = info['cmdline']
            server_type = detect_server_type(name, cmdline)
            
            if server_type:
                ports = []
                # Check default port for this server type
                default_port = default_ports.get(server_type)
                if default_port and not is_port_available(default_port):
                    ports.append(default_port)
                
                servers.append({
                    'pid': info['pid'],
                    'name': name,
                    'type': server_type,
                    'ports': sorted(ports) if ports else [],
                    'command': get_short_command(cmdline)
                })
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    return servers

@click.command()
@click.argument('action', type=click.Choice(['list', 'stop']), default='list')
@click.argument('name', required=False)
def servers(action: str, name: Optional[str]):
    """List running servers and their ports"""
    if action == 'list':
        local_servers = get_all_servers()
        
        # Only try to get Docker containers if Docker is available
        docker_available = shutil.which('docker') is not None
        containers = get_docker_containers() if docker_available else {}
        
        if not local_servers and not containers:
            click.echo("No servers found running")
            return
            
        if local_servers:
            click.echo("\n🖥️  Local Servers:")
            # Sort servers by type, with known types first
            local_servers.sort(key=lambda s: ('unknown' in s['type'], 'generic' in s['type'], s['type']))
            for server in local_servers:
                ports_str = ', '.join(str(p) for p in server['ports']) if server['ports'] else 'no ports detected'
                click.echo(f"- {server['type'].upper()} (PID: {server['pid']}) on port(s) {ports_str}")
                click.echo(f"  Command: {server['command']}")
                
        if containers:
            click.echo("\n🐳 Docker Containers:")
            for container in containers.values():
                click.echo(f"- {container['name']} ({container['status']})")
                if container['ports']:
                    click.echo(f"  Ports: {container['ports']}")
                    
    elif action == 'stop':
        if not name:
            click.echo("Please specify a server name or PID to stop")
            return
            
        try:
            pid = int(name)
            process = psutil.Process(pid)
            process.terminate()
            click.echo(f"Server with PID {pid} has been stopped")
        except ValueError:
            # Name is not a PID, try to find by server type
            servers = get_all_servers()
            matching_servers = [s for s in servers if s['type'].lower() == name.lower()]
            
            if not matching_servers:
                click.echo(f"No running server found with name {name}")
                return
                
            for server in matching_servers:
                try:
                    process = psutil.Process(server['pid'])
                    process.terminate()
                    click.echo(f"Server {name} (PID: {server['pid']}) has been stopped")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    click.echo(f"Failed to stop server {name} (PID: {server['pid']})")
