"""
Command module for the CLI application.
"""
from .ansi import ansi
from .art import art
from .ask import ask
from .code import code
from .process import kill
from .roast import roastme
from .scrape import scrape
from .server import servers
from .system import system
from .view import view
from .write import write
from .research import research  # Keep this here!

__all__ = [
    'ansi',
    'art',
    'ask',
    'code',
    'kill',
    'roastme',
    'scrape',
    'servers',
    'system',
    'view',
    'write',
    'research',
]
