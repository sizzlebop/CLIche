"""
View command for CLIche.
Provides a way to view generated files with proper formatting.
"""
import click
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from ..core import cli
from ..utils.file import get_output_dir, get_docs_dir

@cli.command()
@click.argument('filename')
@click.option('--format', '-f', type=click.Choice(['code', 'write', 'research', 'scrape', 'docs']), default='docs',
              help='Format/location of the file (code, write, research, scrape, or docs)')
@click.option('--source', '-s', type=click.Choice(['write', 'research', 'scrape']), 
              help='Optional source directory within docs (required only when format=docs)')
def view(filename: str, format: str, source: str = None):
    """View a generated file with proper formatting.
    
    Examples:
        cliche view tutorial.md --format write
        cliche view game.py --format code
        cliche view research_commands_in_linux.md --format docs --source research
        cliche view python_async_markdown.md --format docs --source scrape
        
    You can also just use `cliche view filename.md` which will search in the docs directory.
    """
    # Get the appropriate directory
    if format == 'docs':
        if source:
            output_dir = get_docs_dir(source)
        else:
            # If no source specified, search in the main docs directory
            output_dir = get_docs_dir()
    else:
        # Backward compatibility with old structure
        output_dir = get_output_dir(format)
    
    # Find the file
    file_path = output_dir / filename
    if not file_path.exists():
        # Try with just the base name
        matches = list(output_dir.glob(f"*{filename}*"))
        if not matches:
            # If no matches and we're in docs without a source, try searching in all subdirectories
            if format == 'docs' and not source:
                for subdir in ['write', 'research', 'scrape']:
                    subdir_path = get_docs_dir(subdir)
                    submatches = list(subdir_path.glob(f"*{filename}*"))
                    if submatches:
                        matches.extend(submatches)
            
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
