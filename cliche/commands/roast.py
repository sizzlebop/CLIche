"""
Roast command for generating snarky roasts

Generate a snarky, witty roast. Because sometimes you just need to be taken down a notch.
"""
import asyncio
import click
from ..core import cli, CLIche
from ..prompts import ROAST_PROMPT

@cli.command()
def roastme():
    """Get a snarky roast. Because sometimes you just need to be taken down a notch."""
    assistant = CLIche()
    response = asyncio.run(assistant.ask_llm(ROAST_PROMPT))
    # Clean up the response
    response = response.strip().strip('"')  # Remove double quotes
    if not response.startswith("'"):
        response = f"'{response}"  # Add opening single quote if missing
    if not response.endswith("'"):
        response = f"{response}'"  # Add closing single quote if missing
    # Remove any extra roasts or explanations
    if '\n' in response:
        response = response.split('\n')[0]
    click.echo(f" {response}")
