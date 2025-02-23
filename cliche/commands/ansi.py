"""
ANSI art commands
"""
import click
import random
from .ansi_art import ANSI_ART
from ..core import cli

@cli.command()
def ansi():
    """Generate a random ANSI art"""
    art = random.choice(ANSI_ART)
    click.echo(art)
