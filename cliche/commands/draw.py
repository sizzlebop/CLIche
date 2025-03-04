"""Drawing tool for CLIche - uses local Durdraw installation."""
import os
import sys
import click
import subprocess
from pathlib import Path

from ..core import cli

# Path to the local Durdraw installation
DURDRAW_PATH = Path(__file__).parent.parent.parent / "draw"

@cli.command()
@click.option("--width", "-w", default=80, help="Canvas width")
@click.option("--height", "-h", default=24, help="Canvas height")
@click.option("--output", "-o", help="Output file path")
@click.option("--ascii", "-a", is_flag=True, help="Use ASCII art mode (text characters)")
@click.option("--ansi", "-n", is_flag=True, help="Use ANSI art mode (colored blocks)")
def draw(width: int, height: int, output: str = None, ascii: bool = False, ansi: bool = False):
    """
    Create ASCII and ANSI art with Durdraw.
    
    A full-featured terminal-based ASCII and ANSI art editor with:
    
    - Block selection and manipulation
    - Line and box drawing tools
    - 256 color support
    - Animation capabilities
    - Copy/paste, fill, and more
    
    Two distinct modes are available:
    
    1. ASCII Art (--ascii): Uses text characters (#@*+) for simple text art
    
    2. ANSI Art (--ansi): Uses colored block characters (█▓▒░) with 
       up to 256 colors for detailed pixel art
    
    Press F1 within the editor for full help and keyboard shortcuts.
    
    Examples:
      cliche draw              # Start the drawing editor
      cliche draw --ascii      # Start with ASCII mode
      cliche draw --ansi       # Start with ANSI mode 
      cliche draw -w 100 -h 40 # Custom canvas size
    """
    # Path to the Durdraw script
    durdraw_script = DURDRAW_PATH / "durdraw.py"
    
    # If the script doesn't exist, try the executable directly
    if not durdraw_script.exists():
        durdraw_script = DURDRAW_PATH / "start-durdraw"
        
        # If that doesn't exist either, look for the module structure
        if not durdraw_script.exists():
            # Add the Durdraw directory to the Python path
            sys.path.insert(0, str(DURDRAW_PATH))
            try:
                from durdraw import main
                # Build arguments as a list for main function
                args = []
                if width != 80:
                    args.extend(['-W', str(width)])
                if height != 24:
                    args.extend(['-H', str(height)])
                if ansi:
                    args.append('--256color')
                elif ascii:
                    args.append('--16color')
                if output:
                    args.append(output)
                
                # Run Durdraw directly
                sys.argv = [sys.argv[0]] + args
                main()
                return
            except ImportError:
                click.echo("Error: Could not find Durdraw in the expected location.")
                return
    
    # Build command arguments for subprocess
    cmd = [sys.executable, str(durdraw_script)]
    
    # Add width and height options
    if width != 80:
        cmd.extend(['-W', str(width)])
    if height != 24:
        cmd.extend(['-H', str(height)])
    
    # Add mode options
    if ansi:
        cmd.append('--256color')  # Durdraw uses 256 color mode for ANSI art
    elif ascii:
        cmd.append('--16color')   # 16 color is better for ASCII art
        
    # Add output file if specified
    if output:
        cmd.append(output)
    
    try:
        # Run Durdraw
        click.echo("Starting Durdraw editor...")
        subprocess.run(cmd)
        
    except Exception as e:
        click.echo(f"Error running Durdraw: {str(e)}")
        click.echo("Check if Python is properly installed.")

if __name__ == "__main__":
    draw() 