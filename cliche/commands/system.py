"""
System-related commands
"""
import click
import psutil
import platform
from datetime import datetime
from ..utils.gpu import get_gpu_info
from ..utils.docker import get_docker_containers

@click.command()
def system():
    """Display system information"""
    cpu_count = psutil.cpu_count()
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    gpu_name, gpu_usage = get_gpu_info()
    
    click.echo("\n🖥️  System Information:")
    click.echo(f"OS: {platform.system()} {platform.release()}")
    click.echo(f"CPU Cores: {cpu_count}")
    click.echo(f"CPU Usage: {cpu_usage}%")
    click.echo(f"Memory: {memory.used/1024/1024/1024:.1f}GB used of {memory.total/1024/1024/1024:.1f}GB ({memory.percent}%)")
    click.echo(f"Disk: {disk.used/1024/1024/1024:.1f}GB used of {disk.total/1024/1024/1024:.1f}GB ({disk.percent}%)")
    
    if gpu_name != "No GPU detected":
        click.echo(f"GPU: {gpu_name}")
        click.echo(f"GPU Usage: {gpu_usage}")
        
    docker_containers = get_docker_containers()
    if docker_containers:
        click.echo("\n🐳 Docker Containers:")
        for container in docker_containers.values():
            click.echo(f"- {container['name']} ({container['status']})")
            
    click.echo(f"\nCurrent Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
