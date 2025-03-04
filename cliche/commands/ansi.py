"""
ANSI art command for displaying custom art collection
"""
import click
from random import choice
from .ansi_art import ANSI_ART
from ..core import cli

@cli.command(hidden=True)  # Hide from help documentation
@click.option('--index', '-i', type=int, help='Index of art to display')
def ansi(index: int = None):
    """Display ANSI art"""
    # Show deprecation warning
    click.secho("⚠️  The 'ansi' command is deprecated and will be removed in a future version.", fg="yellow")
    click.secho("Please use 'cliche create --ansi' instead.", fg="yellow")
    click.echo("")
    
    if index is not None and 0 <= index < len(ANSI_ART):
        click.echo(ANSI_ART[index])
    else:
        # Show random art if no index specified or index out of range
        art = choice(ANSI_ART)
        click.echo(art)
