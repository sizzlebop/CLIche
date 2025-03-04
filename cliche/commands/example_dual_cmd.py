"""
Example implementation of the dual command pattern.

This file demonstrates how to implement a command that supports both:
1. Flag-based invocation (--option)
2. Subcommand-based invocation (option)

This pattern can be applied to any command in CLIche.
"""
import click
from ..core import cli
from ..utils.command_helpers import create_dual_command, dual_command, option

# Method 1: Using the create_dual_command function

def show_cmd():
    """Show all files in the system."""
    click.echo("Showing all files...")

def list_cmd():
    """List files in a specific format."""
    click.echo("Listing files in formatted view...")

def cleanup_cmd():
    """Clean up old or unused files."""
    click.echo("Cleaning up files...")

# Define options configuration
options = {
    "show": {"is_flag": True, "help": "Show all files"},
    "list": {"is_flag": True, "help": "List files in formatted view"},
    "cleanup": {"is_flag": True, "help": "Clean up old or unused files"},
}

# Create the dual command
files_cmd = create_dual_command(
    name="files",
    help_text="Manage files in the system",
    options=options,
    command_functions={
        "show": show_cmd,
        "list": list_cmd,
        "cleanup": cleanup_cmd
    }
)

# Method 2: Using the class-based approach with decorators

@dual_command(name="example", help_text="Example dual command implementation")
class ExampleCommands:
    @option(is_flag=True, help="Show version information")
    def version(self):
        """Show version information."""
        click.echo("CLIche version 1.0.0")
    
    @option(is_flag=True, help="Show system status")
    def status(self):
        """Show system status."""
        click.echo("All systems operational")
    
    @option(is_flag=True, help="Check for updates")
    def check(self):
        """Check for updates."""
        click.echo("Checking for updates...")

# Register commands with CLI
# Note: In a real implementation, you would add these to __init__.py
# cli.add_command(files_cmd)
# cli.add_command(ExampleCommands)

# Usage examples:
"""
Both of these commands now support:

Flag style:
    cliche files --show 
    cliche files --list
    cliche files --cleanup
    
    cliche example --version
    cliche example --status
    cliche example --check

Subcommand style:
    cliche files show
    cliche files list
    cliche files cleanup
    
    cliche example version
    cliche example status
    cliche example check
""" 