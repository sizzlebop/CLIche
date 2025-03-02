"""
Command module for the CLI application.
"""
from .ansi import ansi
from .art import art
from .ask import ask
from .code import code
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
from .create import create

__all__ = [
    'ansi',
    'art',
    'ask',
    'code',
    'image',
    'kill',
    'roastme',
    'scrape',
    'search',
    'servers',
    'system',
    'view',
    'write',
    'research',
    'create',
]
