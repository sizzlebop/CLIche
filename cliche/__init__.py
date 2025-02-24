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

cli.add_command(config)
cli.add_command(models)
cli.add_command(servers)
cli.add_command(kill)
cli.add_command(ask)
cli.add_command(art)
cli.add_command(ansi)
cli.add_command(roastme)
cli.add_command(system)
cli.add_command(code)
cli.add_command(write)

__version__ = "0.1.0"
__all__ = ['cli']