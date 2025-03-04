"""
Command registry for CLIche CLI tool
"""
from .ansi import ansi
from .art import art
from .ask import ask
from .code import code
from .create import create
from .image import image
from .process import kill
from .roast import roastme
from .scrape import scrape
from .search import search
from .server import servers
from .system import system
from .view import view
from .write import write
from .research import research
from .draw import draw

def register_commands(cli):
    """Register all commands with the CLI."""
    # Import config commands here to avoid circular dependency
    from .config import config, models
    
    cli.add_command(ansi)
    cli.add_command(art)
    cli.add_command(ask)
    cli.add_command(code)
    cli.add_command(config)
    cli.add_command(create)
    cli.add_command(image)
    cli.add_command(kill)
    cli.add_command(models)
    cli.add_command(roastme)
    cli.add_command(scrape)
    cli.add_command(search)
    cli.add_command(servers)
    cli.add_command(system)
    cli.add_command(view)
    cli.add_command(write)
    cli.add_command(research)
    cli.add_command(draw)
