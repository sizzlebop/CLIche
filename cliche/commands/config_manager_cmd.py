"""
Config manager command for CLIche
"""
import click
import json
from pathlib import Path
from ..utils import config_manager

@click.group(name="config-manager", help="Manage CLIche configuration files")
def config_manager_cmd():
    """Manage CLIche configuration files."""
    pass

@config_manager_cmd.command(name="create", help="Create a new config file if it doesn't exist")
def create_config():
    """Create a new config file with default values if it doesn't exist."""
    created = config_manager.ensure_config_exists()
    if created:
        click.echo(f"Created new config file at {config_manager.get_config_path()}")
    else:
        click.echo(f"Config file already exists at {config_manager.get_config_path()}")

@config_manager_cmd.command(name="backup", help="Create a backup of the current config file")
def backup_config():
    """Create a backup of the current config file."""
    backup_path = config_manager.backup_config()
    if backup_path:
        click.echo(f"Created backup at {backup_path}")
    else:
        click.echo("No config file to backup or backup failed.")

@config_manager_cmd.command(name="show", help="Show the current config file content")
def show_config():
    """Show the current config file content."""
    config_path = config_manager.get_config_path()
    if not config_path.exists():
        click.echo("Config file does not exist.")
        return
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Mask API keys for security
        for provider, settings in config.get("providers", {}).items():
            if "api_key" in settings and settings["api_key"] not in ["", "your_api_key_here"]:
                settings["api_key"] = f"***{settings['api_key'][-4:]}" if len(settings["api_key"]) > 4 else "****"
        
        # Pretty print
        click.echo(json.dumps(config, indent=2))
    except Exception as e:
        click.echo(f"Error reading config file: {e}")

@config_manager_cmd.command(name="reset", help="Reset config file to default values")
@click.confirmation_option(prompt="This will overwrite your current config with default values. Continue?")
def reset_config():
    """Reset config file to default values."""
    # Backup first
    backup_path = config_manager.backup_config()
    if backup_path:
        click.echo(f"Created backup at {backup_path}")
    
    # Save default config
    config_manager.save_config(config_manager.DEFAULT_CONFIG)
    click.echo(f"Reset config file to default values at {config_manager.get_config_path()}")

@config_manager_cmd.command(name="edit", help="Open config file in an editor")
def edit_config():
    """Open config file in an editor."""
    config_manager.ensure_config_exists()
    click.edit(filename=str(config_manager.get_config_path())) 