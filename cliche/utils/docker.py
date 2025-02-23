"""
Docker-related utility functions
"""
import json
import subprocess
from typing import Dict

def get_docker_containers() -> Dict:
    """Get list of running docker containers with their details."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{json .}}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {}
            
        containers = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    container = json.loads(line)
                    containers[container['ID']] = {
                        'name': container['Names'],
                        'image': container['Image'],
                        'status': container['Status'],
                        'ports': container['Ports']
                    }
                except json.JSONDecodeError:
                    continue
                    
        return containers
    except (subprocess.SubprocessError, FileNotFoundError):
        return {}
