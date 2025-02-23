"""
Roast command for generating snarky roasts

Generate a snarky, witty roast. Because sometimes you just need to be taken down a notch.
"""
import asyncio
import click
from ..core import cli, CLIche

@cli.command()
def roastme():
    """Get a snarky roast. Because sometimes you just need to be taken down a notch."""
    assistant = CLIche()
    
    roast_prompt = """Generate a snarky, witty roast. Use these examples as inspiration but create a new one:
    'You have a face that would make onions cry.'
    'I look at you and think, Two billion years of evolution, for this?'
    'I am jealous of all the people that have never met you.'
    'I consider you my sun. Now please get 93 million miles away from here.'
    'If laughter is the best medicine, your face must be curing the world.'
    'You're not simply a drama queen/king. You're the whole royal family.'
    'I was thinking about you today. It reminded me to take out the trash.'
    'You are the human version of cramps.'
    'You haven't changed since the last time I saw you. You really should.'
    'If ignorance is bliss, you must be the happiest person on Earth.'"""

    response = asyncio.run(assistant.ask_llm(roast_prompt))
    # Remove any quotation marks the LLM might add
    response = response.strip().strip('"\'')
    click.echo(f" {response}")
