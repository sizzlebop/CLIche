"""
Core functionality for CLIche CLI tool
"""

import click
import requests
import os
import json
import sys
import random
import psutil
import platform
import asyncio
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from openai import OpenAI
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
            return f"Error: {str(e)}"

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
    click.echo(f"🔥 {random.choice(ROASTS)}")

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

@cli.command()
def servers():
    """List running servers and their ports"""
    connections = psutil.net_connections()
    servers = []
    
    for conn in connections:
        if conn.status == 'LISTEN':
            servers.append(f"Port {conn.laddr.port}: {conn.pid if conn.pid else 'Unknown'}")
    
    if servers:
        click.echo("Running servers:")
        for server in servers:
            click.echo(f"🔌 {server}")
    else:
        click.echo("No servers found. Is this a desert?")

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
