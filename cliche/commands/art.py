"""
ASCII art command for displaying cool art
"""
import click
from random import choice
from art import text2art, FONT_NAMES, ART_NAMES, art as art_func
from ..core import cli

@cli.command(hidden=True)  # Hide from help documentation
@click.argument('text', required=False)
@click.option('--font', '-f', help='Font style to use')
@click.option('--random', '-r', is_flag=True, help='Generate random art')
def art(text: str = None, font: str = None, random: bool = False):
    """Generate ASCII art. Add --random for some crazy patterns!"""
    # Show deprecation warning
    click.secho("⚠️  The 'art' command is deprecated and will be removed in a future version.", fg="yellow")
    click.secho("Please use 'cliche create --ascii' instead.", fg="yellow")
    click.echo("")
    
    if random or not text:
        # Generate random decorative art from built-in patterns
        art_type = choice(ART_NAMES)
        result = art_func(art_type)
        click.echo(result)
    else:
        # Generate text art with random font if none specified
        if not font:
            font = choice(FONT_NAMES)
        try:
            result = text2art(text, font=font)
            click.echo(result)
        except Exception as e:
            click.echo(f" Oops, that art style didn't work out. Try a different font! Error: {e}")
