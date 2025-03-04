"""
Config manager command for CLIche.
Demonstrates the dual command pattern where all options are available both as 
flags (--option) and as subcommands (option).
"""
import click
import json
from pathlib import Path
from ..utils import config_manager

@click.command(name="config-manager", help="Manage CLIche configuration files")
@click.option("--show", is_flag=True, help="Show the current config file content")
@click.option("--create", is_flag=True, help="Create a new config file if it doesn't exist")
@click.option("--backup", is_flag=True, help="Create a backup of the current config file")
@click.option("--reset", is_flag=True, help="Reset config file to default values")
@click.option("--edit", is_flag=True, help="Open config file in an editor")
def config_manager_cmd(show, create, backup, reset, edit):
    """Manage CLIche configuration files."""
    # Process options
    if show:
        _show_config()
        return
    
    if create:
        _create_config()
        return
    
    if backup:
        _backup_config()
        return
    
    if reset:
        if click.confirm("This will overwrite your current config with default values. Continue?"):
            _reset_config()
        return
    
    if edit:
        _edit_config()
        return
    
    # If no options specified, show help
    ctx = click.get_current_context()
    click.echo(ctx.get_help())

def _create_config():
    """Create a new config file with default values if it doesn't exist."""
    created = config_manager.ensure_config_exists()
    if created:
        click.echo(f"Created new config file at {config_manager.get_config_path()}")
    else:
        click.echo(f"Config file already exists at {config_manager.get_config_path()}")

def _backup_config():
    """Create a backup of the current config file."""
    backup_path = config_manager.backup_config()
    if backup_path:
        click.echo(f"Created backup at {backup_path}")
    else:
        click.echo("No config file to backup or backup failed.")

def _show_config():
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

def _reset_config():
    """Reset config file to default values."""
    # Backup first
    backup_path = config_manager.backup_config()
    if backup_path:
        click.echo(f"Created backup at {backup_path}")
    
    # Save default config
    config_manager.save_config(config_manager.DEFAULT_CONFIG)
    click.echo(f"Reset config file to default values at {config_manager.get_config_path()}")

def _edit_config():
    """Open config file in an editor."""
    config_manager.ensure_config_exists()
    click.edit(filename=str(config_manager.get_config_path())) 