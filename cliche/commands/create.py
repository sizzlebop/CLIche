"""
Unified create command for CLIche.
Consolidates ASCII art, ANSI art, and other creation tools.
"""
import click
from random import choice
from art import text2art, FONT_NAMES, ART_NAMES, art as art_func
from .ansi_art import ANSI_ART
from ..core import cli

@cli.command()
@click.argument('text', required=False)
@click.option('--ascii', '-a', is_flag=True, help='Generate ASCII text art')
@click.option('--ansi', '-n', is_flag=True, help='Display ANSI art')
@click.option('--font', '-f', help='Font style to use for ASCII art')
@click.option('--random', '-r', is_flag=True, help='Generate random art')
@click.option('--list-fonts', '-l', is_flag=True, help='List available ASCII art fonts')
@click.option('--index', '-i', type=int, help='Index of ANSI art to display')
@click.option('--banner', '-b', is_flag=True, help='Generate a banner-style text')
def create(text: str = None, ascii: bool = False, ansi: bool = False, 
           font: str = None, random: bool = False, list_fonts: bool = False,
           index: int = None, banner: bool = False):
    """Generate ASCII or ANSI art.
    
    Examples:
      cliche create --ascii "Hello"       # Generate ASCII text art
      cliche create --ansi                # Show random ANSI art
      cliche create --ascii --random      # Display random ASCII decorative art
      cliche create --ascii "Hi" --font block # Use specific font
      cliche create --list-fonts          # List available fonts
      cliche create --banner "My Project" # Generate a banner-style header
      cliche create "Cool"                # Default to ASCII text art if text provided
    """
    # List available fonts if requested
    if list_fonts:
        click.echo("Available ASCII art fonts:")
        for i, font_name in enumerate(sorted(FONT_NAMES)):
            if i % 4 == 0:
                click.echo("")
            click.echo(f"{font_name:20}", nl=False)
        click.echo("\n")
        return
    
    # Determine the mode based on flags and arguments
    # Default to ASCII text art if text is provided without flags
    if text and not (ascii or ansi or banner):
        ascii = True
    
    # Default to ANSI art if no text and no specific flags
    if not text and not (ascii or ansi or banner or random):
        ansi = True
    
    # Handle ANSI art
    if ansi:
        if index is not None and 0 <= index < len(ANSI_ART):
            click.echo(ANSI_ART[index])
        else:
            # Show random art if no index specified or index out of range
            art = choice(ANSI_ART)
            click.echo(art)
        return
    
    # Handle ASCII decorative art (random patterns)
    if random and ascii:
        art_type = choice(ART_NAMES)
        result = art_func(art_type)
        click.echo(result)
        return
    
    # Handle ASCII text art or banner
    if text and (ascii or banner):
        # Choose font
        if not font:
            if banner:
                # Use simpler, cleaner fonts for banners
                banner_fonts = ['banner', 'big', 'block', 'standard', 'doom', 'digital', 'ivrit']
                font = choice(banner_fonts)
            else:
                font = choice(FONT_NAMES)
                
        try:
            result = text2art(text, font=font)
            click.echo(result)
        except Exception as e:
            click.echo(f"⚠️ Oops, that font didn't work out. Try a different font! Error: {e}")
        return
    
    # If we got here with no valid options, show help
    if not any([ansi, ascii, banner, random]) or (random and not ascii):
        ctx = click.get_current_context()
        click.echo(ctx.get_help()) 