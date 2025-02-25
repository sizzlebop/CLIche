"""
View command for CLIche.
Provides a way to view generated files with proper formatting.
"""
import click
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from ..core import cli
from ..utils.file import get_output_dir

@cli.command()
@click.argument('filename')
@click.option('--type', '-t', type=click.Choice(['code', 'write']), default='write',
              help='Type of file to view (code or write)')
def view(filename: str, type: str):
    """View a generated file with proper formatting.
    
    Examples:
        cliche view tutorial.md --type write
        cliche view game.py --type code
    """
    # Get the appropriate directory
    output_dir = get_output_dir(type)
    
    # Find the file
    file_path = output_dir / filename
    if not file_path.exists():
        # Try with just the base name
        matches = list(output_dir.glob(f"*{filename}*"))
        if not matches:
            click.echo(f"❌ No file found matching '{filename}' in {output_dir}")
            return 1
        file_path = matches[0]
    
    # Read the file content
    content = file_path.read_text(encoding='utf-8')
    
    # Create a rich console
    console = Console()
    
    # If it's a markdown file, render it with rich's markdown support
    if file_path.suffix in ['.md', '.markdown']:
        markdown = Markdown(content)
        console.print(markdown)
    else:
        # For other files, just print the content
        console.print(content)
    
    return 0
