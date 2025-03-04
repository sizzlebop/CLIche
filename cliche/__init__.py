"""
CLIche: Your terminal's snarky genius assistant
"""
from .core import cli
from .commands.config import config, models
from .commands.ask import ask
from .commands.art import art
from .commands.ansi import ansi
from .commands.roast import roastme
from .commands.system import system
from .commands.process import kill
from .commands.server import servers
from .commands.code import code
from .commands.write import write
from .commands.config_manager_cmd import config_manager_cmd
from .commands.research import research
from .commands.search import search
from .commands.create import create
from .commands.draw import draw

# Initialize config management on import
from .utils import config_manager

cli.add_command(config)
cli.add_command(models)
cli.add_command(servers)
cli.add_command(kill)
cli.add_command(ask)
# Removed from help - now part of create command
# cli.add_command(art)
# cli.add_command(ansi)
cli.add_command(roastme)
cli.add_command(system)
cli.add_command(code)
cli.add_command(write)
cli.add_command(config_manager_cmd)
cli.add_command(research)
cli.add_command(search)
cli.add_command(create)
cli.add_command(draw)

__version__ = "0.1.0"
__all__ = ['cli']