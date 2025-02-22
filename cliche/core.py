"""
Core functionality for CLIche CLI tool
"""

import click
import requests
import os
import json
import re
import sys
import random
import psutil
import platform
import asyncio
import subprocess
import shutil
import fnmatch
import stat
from datetime import datetime
from pathlib import Path
from openai import OpenAI
import black
import mdformat
import anthropic
import google.generativeai
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from .art import ANSI_ART, ROASTS

try:
    import py3nvml as nvml
    HAS_NVIDIA = True
except ImportError:
    HAS_NVIDIA = False

def get_gpu_info() -> Tuple[str, str]:
    """Get GPU information and utilization."""
    try:
        # Try nvidia-smi first
        result = subprocess.run(['nvidia-smi', '--query-gpu=gpu_name,utilization.gpu', '--format=csv,noheader,nounits'],
                            capture_output=True, text=True, check=True)
        if result.stdout.strip():
            gpu_name, utilization = result.stdout.strip().split(',')
            return gpu_name.strip(), f"{utilization.strip()}%"
    except (subprocess.SubprocessError, FileNotFoundError):
        # If nvidia-smi fails, try py3nvml
        if HAS_NVIDIA:
            try:
                nvml.nvmlInit()
                handle = nvml.nvmlDeviceGetHandleByIndex(0)
                name = nvml.nvmlDeviceGetName(handle)
                util = nvml.nvmlDeviceGetUtilizationRates(handle)
                nvml.nvmlShutdown()
                return name, f"{util.gpu}%"
            except Exception:
                pass

        # Try lspci as a last resort
        try:
            result = subprocess.run('lspci | grep -i "vga\\|3d\\|display"', 
                                shell=True, capture_output=True, text=True)
            if result.stdout:
                return result.stdout.strip().split(':')[-1].strip(), "N/A"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    return "No GPU detected", "N/A"

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class Config:
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'cliche'
        self.config_file = self.config_dir / 'config.json'
        self.config = self.load_config()

    def load_config(self) -> Dict:
        if not self.config_file.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            return self.get_default_config()
        
        with open(self.config_file) as f:
            return json.load(f)

    def get_default_config(self) -> Dict:
        default_config = {
            "active_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "",
                    "model": "gpt-4o",
                    "max_tokens": 150
                },
                "anthropic": {
                    "api_key": "",
                    "model": "claude-3.5-sonnet",
                    "max_tokens": 150
                },
                "google": {
                    "api_key": "",
                    "model": "gemini-2.0-flash"
                },
                "deepseek": {
                    "api_key": "",
                    "model": "deepseek-chat"
                },
                "openrouter": {
                    "api_key": "",
                    "model": "openrouter/auto"
                },
                "ollama": {
                    "host": "http://localhost:11434",
                    "model": "Llama3.2:3b"
                }
            },
            "personality": "snarky, witty, encyclopedic, slightly sarcastic, helpful, knowledgeable"
        }
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict) -> None:
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_provider_config(self, provider: str) -> Dict:
        return self.config["providers"].get(provider, {})

class LLMBase:
    def __init__(self, config: Dict):
        self.config = config

    async def generate_response(self, query: str) -> str:
        raise NotImplementedError

class OpenAIProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.client = OpenAI(api_key=config.get('api_key') or os.getenv('OPENAI_API_KEY'))
        
    def get_system_context(self) -> str:
        """Get current system context including time, date, and system info."""
        current_time = datetime.now().strftime("%I:%M %p")
        current_date = datetime.now().strftime("%B %d, %Y")
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        gpu_name, gpu_usage = get_gpu_info()

        context = f"""You are a snarky terminal assistant. Some current system information:
- Current time: {current_time}
- Current date: {current_date}
- CPU Usage: {cpu_usage}%
- Memory Usage: {memory}%
- OS: {platform.system()} {platform.release()}"""

        if gpu_name != "No GPU detected":
            context += f"\n- GPU: {gpu_name} (Usage: {gpu_usage})"

        context += "\n\nPlease provide concise, slightly sarcastic responses. Reference this system information only when relevant."
        return context

    async def generate_response(self, query: str) -> str:
        try:                 
            response = self.client.chat.completions.create(
                model=self.config['model'],
                user=f"{query}\n\nSystem Context:\n{self.get_system_context()}", 
                messages=[
                    {"role": "system", "content": "You are a snarky, witty terminal assistant with encyclopedic and technical knowledge, as well as knowledge in pop culture, art, film and music. You are great at writing detailed documents on any subject when asked. Keep responses concise and slightly sarcastic."},
                    {"role": "user", "content": query}
                ],
                max_tokens=self.config.get('max_tokens', 150)
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI Error: {str(e)}"

class AnthropicProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.client = anthropic.Client(api_key=config.get('api_key') or os.getenv('ANTHROPIC_API_KEY'))
        
    def get_system_context(self) -> str:
        """Get current system context including time, date, and system info."""
        current_time = datetime.now().strftime("%I:%M %p")
        current_date = datetime.now().strftime("%B %d, %Y")
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        gpu_name, gpu_usage = get_gpu_info()

        context = f"""You are a snarky terminal assistant. Some current system information:
- Current time: {current_time}
- Current date: {current_date}
- CPU Usage: {cpu_usage}%
- Memory Usage: {memory}%
- OS: {platform.system()} {platform.release()}"""

        if gpu_name != "No GPU detected":
            context += f"\n- GPU: {gpu_name} (Usage: {gpu_usage})"

        context += "\n\nPlease provide concise, slightly sarcastic responses. Reference this system information only when relevant."
        return context

    async def generate_response(self, query: str) -> str:
        try:
            response = self.client.Completion.create(
                engine=self.config['model'],
                prompt=f"{query}\n\nSystem Context:\n{self.get_system_context()}",                
                messages=[
                    {"role": "system", "content": "You are a snarky, witty terminal assistant with encyclopedic and technical knowledge, as well as knowledge in pop culture, art, film and music. You are great at writing detailed documents on any subject when asked. Keep responses concise and slightly sarcastic."},
                    {"role": "user", "content": query}
                ],
                max_tokens=self.config.get('max_tokens', 150)
            )           
            return response.content[0].message.content
        except Exception as e:
            return f"Anthropic Error: {str(e)}"
        
class GoogleProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.client = google.generativeai.ChatClient(api_key=config.get('api_key') or os.getenv('GOOGLE_API_KEY'))
        
    def get_system_context(self) -> str:
        """Get current system context including time, date, and system info."""
        current_time = datetime.now().strftime("%I:%M %p")
        current_date = datetime.now().strftime("%B %d, %Y")
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        gpu_name, gpu_usage = get_gpu_info()

        context = f"""You are a snarky terminal assistant. Some current system information:
- Current time: {current_time}
- Current date: {current_date}
- CPU Usage: {cpu_usage}%
- Memory Usage: {memory}%
- OS: {platform.system()} {platform.release()}"""

        if gpu_name != "No GPU detected":
            context += f"\n- GPU: {gpu_name} (Usage: {gpu_usage})"

        context += "\n\nPlease provide concise, slightly sarcastic responses. Reference this system information only when relevant."
        return context
        
    async def generate_response(self, query: str) -> str:
        try:
            system_context = self.get_system_context()
            response = await self.client.predict_response(
                model=self.config['model'],
                user_input=f"{query}\n\nSystem Context:\n{self.get_system_context()}",          
                temperature=0.9,
                messages=[
                    {"role": "system", "content": "You are a snarky, witty terminal assistant with encyclopedic and technical knowledge, as well as knowledge in pop culture, art, film and music. You are great at writing detailed documents on any subject when asked. Keep responses concise and slightly sarcastic."},
                    {"role": "user", "content": query}
                ],
                max_tokens=self.config.get('max_tokens', 500)
            )
            return response.content[0].message.content
        except Exception as e:
            return f"Google Error: {str(e)}"

class OllamaProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.host = config.get('host', 'http://localhost:11434')

    def get_system_context(self) -> str:
        """Get current system context including time, date, and system info."""
        current_time = datetime.now().strftime("%I:%M %p")
        current_date = datetime.now().strftime("%B %d, %Y")
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        gpu_name, gpu_usage = get_gpu_info()

        context = f"""You are a snarky terminal assistant. Some current system information:
- Current time: {current_time}
- Current date: {current_date}
- CPU Usage: {cpu_usage}%
- Memory Usage: {memory}%
- OS: {platform.system()} {platform.release()}"""

        if gpu_name != "No GPU detected":
            context += f"\n- GPU: {gpu_name} (Usage: {gpu_usage})"

        context += "\n\nPlease provide concise, slightly sarcastic responses. Reference this system information only when relevant."
        return context

    async def generate_response(self, query: str) -> str:
        try:
            system_context = self.get_system_context()
            full_prompt = f"{system_context}\n\nUser: {query}\n\nYou are a snarky, witty terminal assistant with encyclopedic and technical knowledge, as well as knowledge in pop culture, art, film and music. You are great at writing detailed documents on any subject when asked. Keep responses concise and slightly sarcastic.\nAssistant:"
            
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.config['model'],
                    "prompt": full_prompt,
                    "stream": False,
                    "system": system_context
                }
            )
            
            if response.status_code == 404:
                models_response = requests.get(f"{self.host}/api/tags")
                available_models = [model['name'] for model in models_response.json()['models']]
                return f"Model {self.config['model']} not found. Available models: {', '.join(available_models)}"
            
            return response.json()['response']
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Is it running? Install from https://ollama.ai and run 'ollama serve'"
        except Exception as e:
            return f"Ollama Error: {str(e)}"

class CLIche:
    def __init__(self):
        self.config = Config()
        self.provider = self._get_provider()

    def _get_provider(self) -> LLMBase:
        active_provider = self.config.config.get('active_provider', 'openai')
        provider_config = self.config.get_provider_config(active_provider)
        
        providers = {
            'openai': OpenAIProvider,
            'anthropic': AnthropicProvider,
            'google': GoogleProvider,
            'ollama': OllamaProvider
        }
        
        provider_class = providers.get(active_provider)
        if provider_class:
            return provider_class(provider_config)
        else:
            raise ValueError(f"Unsupported provider: {active_provider}")

    async def ask_llm(self, query: str) -> str:
        try:
            return await self.provider.generate_response(query)
        except Exception as e:
            return f"Error: Unable to generate content. Please check your provider configuration with 'cliche config --help'"

@click.group()
def cli():
    """CLIche: Your terminal's snarky genius assistant"""
    pass

@cli.command()
@click.argument('query', nargs=-1)
def ask(query):
    """Ask CLIche anything"""
    if not query:
        click.echo("Error: No query provided, genius. Please type something!")
        return

    query_str = " ".join(query)
    click.echo("🤔 CLIche is pondering (and judging)...")
    
    assistant = CLIche()
    response = asyncio.run(assistant.ask_llm(query_str))
    click.echo(f"\n💡 {response}")

@cli.command()
def ansi():
    """Generate a random ANSI art"""
    click.echo(random.choice(ANSI_ART))

@cli.command()
def roastme():
    """Get a programming roast"""
    assistant = CLIche()
    roast_prompt = "Generate a snarky, witty roast. Use the example roasts as inspiration but create a completely new one: 'You have a face that would make onions cry.' 'I look at you and think, Two billion years of evolution, for this?' 'I am jealous of all the people that have never met you.' 'I consider you my sun. Now please get 93 million miles away from here.' 'If laughter is the best medicine, your face must be curing the world.' 'You're not simply a drama queen/king. You're the whole royal family.' 'I was thinking about you today. It reminded me to take out the trash.' 'You are the human version of cramps.' 'You haven't changed since the last time I saw you. You really should.''If ignorance is bliss, you must be the happiest person on Earth.'"

    response = asyncio.run(assistant.ask_llm(roast_prompt))
    # Remove any quotation marks the LLM might add
    response = response.strip().strip('"\'')
    click.echo(f"🔥 {response}")

@cli.command()
def sysinfo():
    """Display system information"""
    gpu_name, gpu_usage = get_gpu_info()
    
    info = {
        "OS": platform.system() + " " + platform.release(),
        "Python": sys.version.split()[0],
        "CPU Usage": f"{psutil.cpu_percent()}%",
        "Memory": f"{psutil.virtual_memory().percent}% used",
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Active LLM": Config().config.get('active_provider', 'openai')
    }
    
    if gpu_name != "No GPU detected":
        info["GPU"] = f"{gpu_name} (Usage: {gpu_usage})"
    
    for key, value in info.items():
        click.echo(f"{key}: {value}")

def get_process_name(pid):
    """Get process name for a given PID."""
    try:
        process = psutil.Process(pid)
        return process.name(), process.cmdline()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "Unknown", []

def get_service_default_ports():
    """Return a mapping of services to their default ports."""
    return {
        'ollama': 11434,
        'jupyter': [8888, 8889],
        'mysql': 3306,
        'postgresql': 5432,
        'mongodb': 27017,
        'redis': 6379,
        'elasticsearch': 9200,
        'cassandra': 9042,
        'rabbitmq': 5672,
        'kafka': 9092,
        'nginx': [80, 443],
        'apache': [80, 443],
        'next.js': 3000,
        'vite': 5173,
        'webpack': 8080,
        'streamlit': 8501,
        'fastapi': 8000,
        'django': 8000,
        'flask': 5000
    }

def is_port_available(port):
    """Check if a port is likely being used by a service."""
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return False
        return True
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return False

def is_system_port(port):
    """Check if a port is likely a system port we want to filter out."""
    return port < 20  # Only filter out very low system ports

def get_short_command(cmdline):
    """Get a simplified version of the command."""
    return ' '.join(cmdline[:2]) if cmdline else 'Unknown'

def get_docker_containers():
    """Get list of running docker containers with their details."""
    containers = {}
    try:
        result = subprocess.run(['docker', 'ps', '--format', '{{.ID}}\t{{.Image}}\t{{.Ports}}\t{{.Names}}'],
                              capture_output=True, text=True, check=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    cid, image, ports, name = line.split('\t')
                    port_list = []
                    if ports:
                        # Extract port numbers from Docker port mappings
                        port_matches = re.findall(r':(\d+)->', ports)
                        port_list = [int(p) for p in port_matches]
                    containers[cid] = {
                        'image': image,
                        'ports': port_list,
                        'name': name
                    }
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return containers

docker_containers = get_docker_containers()
running_container_names = set(c['name'] for c in docker_containers.values())

def detect_server_type(name, cmdline):
    """Detect the type of server based on process name and command line."""
    name = name.lower()
    cmdline_str = ' '.join(cmdline).lower()

    # Organize server types by categories
    SERVER_CATEGORIES = {
        'Web Servers': {
            'nginx': ['nginx'],
            'apache': ['apache2', 'httpd'],
        },
        
        'Databases': {
            'mysql': ['mysqld', 'mariadb', 'mysql.server'],
            'postgresql': ['postgres', 'postgresql'],
            'redis': ['redis-server', 'redis-server.exe'],
            'mongodb': ['mongod', 'mongodb'],
            'elasticsearch': ['elasticsearch'],
            'cassandra': ['cassandra'],
        },
        
        'Application Servers': {
            'node': ['node', 'nodejs', 'npm', 'yarn'],
            'python': ['python', 'python3', 'uwsgi', 'gunicorn'],
            'java': ['java', 'tomcat', 'jetty'],
            'php': ['php-fpm', 'php', 'artisan'],
        },
        
        'Container Services': {
            'docker': ['dockerd', 'docker', 'containerd', 'docker-compose'],
            'ollama': ['ollama'],
            'kubernetes': ['kubelet', 'kubectl', 'k8s'],
        },
        
        'Message Queues': {
            'rabbitmq': ['rabbitmq', 'rabbit'],
            'kafka': ['kafka'],
            'redis-mq': ['redis'],
        },

        'AI/ML Services': {
            'jupyter': ['jupyter', 'jupyter-lab', 'jupyter-notebook'],
        },

        'Development Servers': {
        'next.js': ['next', 'next-server'],
        'vite': ['vite', '@vite/server'],
        'webpack': ['webpack'],
        'parcel': ['parcel'],
        
        # Web Frameworks
        'django': ['django'],
        'flask': ['flask'],
        'fastapi': ['uvicorn', 'fastapi'],
        'express': ['express'],
        'nuxt': ['nuxt'],
        'spring': ['spring-boot'],
        'uvicorn': ['uvicorn'],
        'gunicorn': ['gunicorn'],
        'waitress': ['waitress-serve'],
        'streamlit': ['streamlit'],
        'gatsby': ['gatsby'],
        'vue': ['vue-cli-service'],
        'angular': ['ng serve'],
        }}
    
    # Don't show our own CLI process
    if any(x in cmdline_str for x in ['cliche servers', 'cliche --help']):
        return None
        
    # Don't show system processes
    if any(x in name.lower() for x in ['systemd', 'init', 'upstart', 'launchd']):
        return None
    
    for category, server_types in SERVER_CATEGORIES.items():
        for server_type, patterns in server_types.items():
            if any(pattern in name for pattern in patterns):
                if server_type == 'python' and not any(x in cmdline_str for x in ['server', 'flask', 'django', 'uvicorn', 'gunicorn', 'fastapi']):
                    continue
                if server_type == 'node' and not any(x in cmdline_str for x in ['server', 'express', 'http', 'next', 'nuxt']):
                    continue
                if server_type == 'java' and not any(x in cmdline_str for x in ['tomcat', 'spring', 'server', 'jetty']):
                    continue
                return f"{category}|{server_type}"

    # Check for standalone services that don't fit into categories
    if 'ollama' in name:
        return 'AI/ML Services|ollama'
            
    # Handle npm/yarn dev servers
    if ('npm' in name.lower() or 'yarn' in name.lower()) and any(x in cmdline_str for x in ['dev', 'start', 'serve']):
        if 'next' in cmdline_str:
            return 'next.js'
        return 'dev-server'

    
    # Check command line for server indicators
    if 'server' in cmdline_str or 'serve' in cmdline_str:
        for keyword in ['dev', 'development', 'web', 'api']:
            if keyword in cmdline_str:
                return 'Development Servers|dev-server'
    
    if 'server' in cmdline_str:
        return 'Other Services|generic-server'
    
    return None

def get_all_servers():
    """Get all running server processes regardless of open ports."""
    servers = {}
    default_ports = get_service_default_ports()
    active_ports = {}
    
    # Get all active listening ports first
    try:
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN' and conn.pid and not is_system_port(conn.laddr.port):
                active_ports[conn.pid] = active_ports.get(conn.pid, set()) | {conn.laddr.port}
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        pass
    
    # First check all processes for server-like names
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        # Check Docker containers first
        if docker_containers:
            for container_id, container in docker_containers.items():
                if container['name'] not in [s.get('name') for s in servers.values()]:
                    # Extract service name from image (e.g., mysql:latest -> mysql)
                    service_name = container['image'].split(':')[0].split('/')[-1].lower()
                    servers[f"docker-{container_id}"] = {
                        'type': f'docker-{service_name}',
                        'display_name': container['name'],
                        'name': container['name'],
                        'ports': set(container['ports']),
                        'cmdline': f"docker container: {container['image']}"
                    }

        try:
            if proc.info['pid'] is None:
                continue
                
            name = proc.info['name']
            cmdline = proc.info['cmdline']
            if not cmdline:
                continue

            # Check for virtual env servers
            if any(x in ' '.join(cmdline).lower() for x in ['uvicorn', 'gunicorn', 'waitress', 'flask run']):
                name = 'venv-server'
            
            # Check for known development servers
            if any(x in ' '.join(cmdline).lower() for x in ['dev server', 'development server', 'webpack', 'vite']):
                name = 'dev-server'
            
            # Skip if this is a docker container we already found
            if name in running_container_names:
                continue

            server_type = detect_server_type(name, cmdline)
            if server_type:
                base_type = server_type.split('|')[1] if '|' in server_type else server_type
                ports = set()
                
                # Add active ports for this process
                if proc.info['pid'] in active_ports:
                    ports.update(active_ports[proc.info['pid']])
                    
                # Add default ports if no active ports found
                # Check active network connections
                if proc.info['pid'] in servers:
                    ports.update(servers[proc.info['pid']]['ports'])
                
                # Add known default ports for the service
                if base_type in default_ports:
                    if not ports and isinstance(default_ports[base_type], list):
                        ports.update(default_ports[base_type])
                    elif not ports:
                        ports.add(default_ports[base_type])
                
                servers[proc.info['pid']] = {
                    'type': server_type,
                    'display_name': name,
                    'ports': ports,
                    'cmdline': ' '.join(cmdline) if cmdline else 'Unknown'
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Then add port information from network connections
    connections = psutil.net_connections()
    for conn in [c for c in connections if c.status == 'LISTEN']:
        if conn.status == 'LISTEN' and conn.pid is not None:
            if conn.pid in servers and not is_system_port(conn.laddr.port):
                servers[conn.pid]['ports'].add(conn.laddr.port)
            elif conn.pid not in servers:
                try:
                    proc = psutil.Process(conn.pid)
                    name = proc.name()
                    cmdline = proc.cmdline()
                    server_type = detect_server_type(name, cmdline)
                    if server_type and not is_system_port(conn.laddr.port):
                        servers[conn.pid] = {
                            'type': server_type,
                            'display_name': name,
                            'name': name,
                            'ports': {conn.laddr.port},
                            'cmdline': ' '.join(cmdline) if cmdline else 'Unknown'
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
    
    return servers

@cli.command()
@click.option('--action', type=click.Choice(['list', 'start', 'stop', 'restart']), default='list', help='Action to perform')
@click.option('--name', help='Server name to act on (for start/stop/restart)')
def servers(action, name):
    """List running servers and their ports"""
    if action == 'list':
        servers = get_all_servers()
        
        if servers:
            click.echo("Running servers:")
            # Group servers by category
            categorized_servers = {}
            for pid, info in servers.items():
                server_type = info['type']
                category = 'Other Services'
                service_type = server_type

                if '|' in server_type:
                    category, server_type = server_type.split('|')
                if not category in categorized_servers:
                    categorized_servers[category] = []
                info['server_type'] = server_type
                categorized_servers[category].append((pid, info))

            for category in sorted(categorized_servers.keys()):
                click.echo(f"\n📦 {category}:")
                # Sort servers within category by type
                sorted_servers = sorted(categorized_servers[category], key=lambda x: (x[1]['server_type'], x[1]['display_name']))
                for pid, info in sorted_servers:
                    ports_str = ', '.join(f":{port}" for port in sorted(info['ports']))
                    ports_info = f" [Ports{ports_str}]" if ports_str else ""
                    click.echo(f"  🔌 {info['server_type'].title()}: {info['display_name']}{ports_info}")
                    click.echo(f"     PID: {pid}")
                    click.echo(f"     CMD: {get_short_command(info['cmdline'].split())}")
                    click.echo(f"   To manage: {'docker stop/start ' + info['display_name'] if 'docker-' in info['type'] else 'cliche servers --action [start|stop|restart] --name ' + info['display_name']}")
                click.echo("")
        else:
            if action == 'list':
                click.echo("Pro tip: Some services might need sudo to be visible")
            click.echo("No servers found. Is this a desert? 🏜️")
    
    else:
        if not name:
            click.echo("Error: Please specify a server name for this action")
            return
            
        try:
            result = subprocess.run(['systemctl', action, name], capture_output=True, text=True)
            if result.returncode == 0:
                click.echo(f"Successfully {action}ed {name}")
            else:
                try:
                    # Try service command if systemctl fails
                    result = subprocess.run(['service', name, action], capture_output=True, text=True)
                    if result.returncode == 0:
                        click.echo(f"Successfully {action}ed {name}")
                    else:
                        click.echo(f"Failed to {action} {name}. Are you root?")
                except Exception:
                    click.echo(f"Failed to {action} {name}. Are you root?")
        except Exception as e:
            click.echo(f"Error: {str(e)}")
    

@cli.command()
@click.argument('pid', type=int)
def kill(pid):
    """Kill a process by PID"""
    try:
        process = psutil.Process(pid)
        process.terminate()
        click.echo(f"💀 Process {pid} has been terminated. Another one bites the dust!")
    except psutil.NoSuchProcess:
        click.echo(f"Process {pid} not found. It's already dead, Jim!")
    except psutil.AccessDenied:
        click.echo(f"Nice try, but you don't have permission to kill process {pid}.")

@cli.command()
@click.option('--provider', type=click.Choice([p.value for p in LLMProvider]))
@click.option('--api-key', help='API key for the provider')
@click.option('--model', help='Model to use')
@click.option('--host', help='Host URL for local providers')
@click.option('--personality', help='Assistant personality (snarky/professional)')
def config(provider, api_key, model, host, personality):
    """Configure CLIche settings"""
    config = Config()
    
    if provider:
        config.config['active_provider'] = provider
    if api_key and provider:
        config.config['providers'][provider]['api_key'] = api_key
    if model and provider:
        config.config['providers'][provider]['model'] = model
    if host and provider in ['ollama']:
        config.config['providers'][provider]['host'] = host
    if personality:
        config.config['personality'] = personality

    config.save_config(config.config)
    click.echo("✨ Configuration updated. I'll try to be less judgy (no promises).")

@cli.command()
def models():
    """List available local models"""
    config = Config()
    if config.config['active_provider'] != 'ollama':
        click.echo("This command only works with Ollama provider")
        return
    
    provider_config = config.get_provider_config('ollama')
    host = provider_config.get('host', 'http://localhost:11434')
    
    try:
        response = requests.get(f"{host}/api/tags")
        if response.status_code == 200:
            models = response.json()['models']
            click.echo("\nAvailable models:")
            for model in models:
                click.echo(f"• {model['name']}")
        else:
            click.echo("Error fetching models from Ollama")
    except requests.exceptions.ConnectionError:
        click.echo("Cannot connect to Ollama. Is it running? Install from https://ollama.ai and run 'ollama serve'")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.argument('source')
@click.argument('target')
@click.option('--force', is_flag=True, help='Overwrite target if it exists')
def rename(source, target, force):
    """Rename a file or directory.
    
    SOURCE: Original file or directory name
    TARGET: New file or directory name
    """
    try:
        source_path = Path(source)
        target_path = Path(target)

        if not source_path.exists():
            click.echo(f"Error: '{source}' not found")
            return

        if target_path.exists() and not force:
            click.echo(f"Error: '{target}' already exists. Use --force to overwrite")
            return

        # Handle directory renaming
        if source_path.is_dir():
            if target_path.exists() and force:
                shutil.rmtree(target_path)
            shutil.move(str(source_path), str(target_path))
            click.echo(f"✨ Directory renamed from '{source}' to '{target}'")
            

        
        # Handle file renaming
        else:
            if target_path.exists() and force:
                target_path.unlink()
            shutil.move(str(source_path), str(target_path))
            click.echo(f"✨ File renamed from '{source}' to '{target}'")

    except Exception as e:
        click.echo(f"Error renaming: {str(e)}")

@cli.command()
@click.option('--name', help='Search for files by name (supports wildcards like *.txt)')
@click.option('--type', 'filetype', help='Search for files by extension (e.g., png)')
@click.option('--path', default=str(Path.home()), help='Starting path for search (default: home directory)')
def find(name, filetype, path):
    """Search for files by name or file type.
    
    Examples:
    \b
    Search by name (supports wildcards):
        cliche find --name "*.txt"
        cliche find --name "document*"
    
    Search by file type:
        cliche find --type png
        cliche find --type pdf
    
    Search in specific directory:
        cliche find --name "*.jpg" --path /home/user/Pictures
    """
    try:
        start_path = Path(path)
        if not start_path.exists():
            click.echo(f"Error: Path '{path}' does not exist")
            return

        if not name and not filetype:
            click.echo("Error: Please provide either --name or --type option")
            return

        pattern = name if name else f"*.{filetype}"
        found = False
        
        click.echo(f"🔍 Searching in {start_path}...")
        click.echo("Press Ctrl+C to stop the search")
        
        # Convert to absolute paths without changing user's directory
        if path:
            base_dir = Path(path).resolve()
        else:
            base_dir = (Path.home() / '.cliche' / 'files').resolve()
        
        # Skip system directories that could cause issues
        skip_dirs = {'/proc', '/sys', '/dev', '/run'}
        
        try:
            for filepath in start_path.rglob("*"):
                try:
                    # Skip system directories
                    if any(str(filepath).startswith(skip) for skip in skip_dirs):
                        continue
                        
                    if filepath.is_file() and fnmatch.fnmatch(filepath.name.lower(), pattern.lower()):
                        click.echo(f"📄 {filepath}")
                        found = True
                except (PermissionError, OSError) as e:
                    # Silently skip permission errors
                    continue
        except KeyboardInterrupt:
            click.echo("\n🛑 Search stopped by user")
            return

        if not found:
            click.echo("No matching files found. 🤷")
            
    except Exception as e:
        click.echo(f"Error during search: {str(e)}")
        
@cli.command()
@click.argument('prompt')
@click.option('--type', type=click.Choice(['code', 'text', 'markdown']), required=True, help='Type of content to write')
@click.option('--lang', help='Programming language for code files')
@click.option('--path', help='Directory to save the file')
@click.option('--generate', is_flag=True, help='Generate content from prompt')

def write(prompt, type, lang, path, generate):
    """Write or generate content and save to a file.
    
    Examples:
    \b
    Generate a Python script:
        cliche write "create a web scraper" --type code --lang python --generate
    
    Generate a story:
        cliche write "write a short sci-fi story" --type text --generate
    
    Generate a markdown document:
        cliche write "create a project readme" --type markdown --generate
    
    Write direct content:
        cliche write "Hello World" --type text
    """
    try:
        # Generate content if requested
        content = prompt
        if generate:
            if not prompt:
                click.echo("Error: Please provide a prompt for content generation")
                return
                
            click.echo("🤔 Generating content...")
            assistant = CLIche()
            
            # Create appropriate prompt based on file type
            if type == 'code':
                llm_prompt = f"Write {lang} code that does the following: {prompt}. Only provide the code, no explanations."
            elif type == 'markdown':
                llm_prompt = f"Write a markdown document for: {prompt}. Include proper markdown formatting."
            else:  # text
                llm_prompt = prompt
            
            # Generate content
            content = asyncio.run(assistant.ask_llm(llm_prompt))
            
            if not content or content.startswith("Error:"):
                click.echo(f"Error: Failed to generate content. Please make sure you have configured a provider with 'cliche config --provider [provider] --api-key [key]'")
                return
        
        # Verify we have content to write
        if not content:
            click.echo("Error: No content provided")
            return
            
        # Convert to absolute paths without changing user's directory
        if path:
            base_dir = Path(path).resolve()
        else:
            base_dir = (Path.home() / '.cliche' / 'files').resolve()
            
        # Create subdirectory based on file type
        if type == 'code':
            save_dir = base_dir / 'code' / lang
        else:
            save_dir = base_dir / type
        
        # Create directory with proper permissions
        save_dir.mkdir(parents=True, exist_ok=True)
        # Set directory permissions to 755 (rwxr-xr-x)
        save_dir.chmod(0o755)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Determine file extension and format content
        if type == 'code':
            if lang.lower() == 'python':
                ext = '.py'
                try:
                    content = black.format_str(content, mode=black.FileMode())
                except:
                    pass
            else:
                ext = f'.{lang}'
        elif type == 'markdown':
            ext = '.md'
            try:
                content = mdformat.text(content)
            except:
                pass
        else:  # text
            ext = '.txt'
        
        # Create filename
        if type == 'code':
            filename = f"code_{lang}_{timestamp}{ext}"
        else:
            filename = f"{type}_{timestamp}{ext}"
        
        # Full file path
        file_path = save_dir / filename
        
        # Write content to file
        file_path.write_text(content)
        # Set file permissions to 644 (rw-r--r--)
        file_path.chmod(0o644)
        
        click.echo(f"✨ File created: {file_path}")
        click.echo(f"You can open the file with your preferred editor")
            
    except Exception as e:
        click.echo(f"Error creating file: {str(e)}")
