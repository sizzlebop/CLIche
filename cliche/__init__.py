"""
CLIche: Your terminal's snarky genius assistant
"""
from .core import cli
from .commands.config import config, models
from .commands.server import servers
from .commands.process import kill
from .commands.ask import ask
from .commands.file import rename, find, write
from .commands.system import system
from .commands.ansi import ansi
from .commands.roast import roastme

cli.add_command(config)
cli.add_command(models)
cli.add_command(servers)
cli.add_command(kill)
cli.add_command(ask)
cli.add_command(rename)
cli.add_command(find)
cli.add_command(write)
cli.add_command(system)
cli.add_command(ansi)
cli.add_command(roastme)

__version__ = "0.1.0"
__all__ = ['cli']