"""
View command for CLIche.
Provides a way to view generated files with proper formatting.
"""
import click
import re
import os
import sys
import subprocess
import shutil
import base64
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from ..core import cli
from ..utils.file import get_output_dir, get_docs_dir

# Import image viewing utilities if available
try:
    from .image import view_image, check_terminal_colors
except ImportError:
    # Fallback implementation if image module can't be imported
    def view_image(image_path, width=None, height=None):
        click.echo(f"Image viewing not available. Image at: {image_path}")
        return False
        
    def check_terminal_colors():
        return 8

def extract_markdown_images(content):
    """Extract image references from markdown content.
    
    Returns a list of dictionaries with keys:
        - url: The image URL or file path
        - alt: The alt text for the image
        - width: The image width if specified
        - height: The image height if specified
    """
    # Match standard markdown image syntax: ![alt text](url)
    images = []
    
    # Standard markdown image syntax
    pattern = r'!\[(.*?)\]\((.*?)\)'
    matches = re.findall(pattern, content)
    
    for alt, url in matches:
        # Initialize image data
        image_data = {
            'alt': alt or 'Image',
            'url': url,
            'width': None,
            'height': None
        }
        
        # Check for size specifications in the URL or after it
        # Format: ![alt](url =WIDTHxHEIGHT) or ![alt](url){width=WIDTH height=HEIGHT}
        size_in_url = re.search(r'=(\d+)x(\d+)$', url)
        if size_in_url:
            # Remove the size part from the URL
            image_data['url'] = url[:size_in_url.start()]
            image_data['width'] = int(size_in_url.group(1))
            image_data['height'] = int(size_in_url.group(2))
        else:
            # Look for {width=X height=Y} format after the URL
            width_height_after = re.search(r'\)\{.*?width=(\d+).*?(?:height=(\d+))?.*?\}', content)
            if width_height_after:
                image_data['width'] = int(width_height_after.group(1))
                if width_height_after.group(2):
                    image_data['height'] = int(width_height_after.group(2))
            # Alternative format {height=Y width=X}
            else:
                height_width_after = re.search(r'\)\{.*?height=(\d+).*?(?:width=(\d+))?.*?\}', content)
                if height_width_after:
                    image_data['height'] = int(height_width_after.group(1))
                    if height_width_after.group(2):
                        image_data['width'] = int(height_width_after.group(2))
        
        # Check if the URL is absolute or relative
        if not url.startswith(('http://', 'https://')):
            # It's a relative path, not a full URL
            if os.path.exists(url):
                # Use as is if it exists
                pass
            else:
                # Skip non-existent files
                continue
                
        images.append(image_data)
    
    return images

@cli.command()
@click.argument('filename')
@click.option('--format', '-f', type=click.Choice(['code', 'write', 'research', 'scrape', 'docs']), default='docs',
              help='Format/location of the file (code, write, research, scrape, or docs)')
@click.option('--source', '-s', type=click.Choice(['write', 'research', 'scrape']), 
              help='Optional source directory within docs (required only when format=docs)')
@click.option('--show-images/--hide-images', default=True, 
              help='Display images in markdown documents (default: True)')
@click.option('--image-width', default=100, help='Width for displayed images (in characters, auto-scales height)')
def view(filename: str, format: str, source: str = None, show_images: bool = True, image_width: int = 100):
    """View a generated file with proper formatting.
    
    For markdown files, this command renders the text and can also display any embedded images.
    Images are displayed using intelligent sizing that:
    - Automatically detects actual image dimensions
    - Preserves aspect ratio when only width is specified
    - Uses appropriate terminal-friendly dimensions
    - Shows small images at their original size when appropriate
    
    Examples:
        cliche view tutorial.md --format write
        cliche view game.py --format code
        cliche view research_commands_in_linux.md --format docs --source research
        cliche view python_async_markdown.md --format docs --source scrape
        
    You can also just use `cliche view filename.md` which will search in the docs directory.
    
    For markdown files with images, you can control image display with:
        cliche view document.md --show-images
        cliche view document.md --hide-images
        cliche view document.md --image-width 120
    """
    # Get the appropriate directory
    if format == 'docs':
        if source:
            output_dir = get_docs_dir(source)
        else:
            # If no source specified, search in the main docs directory
            output_dir = get_docs_dir()
    else:
        # Backward compatibility with old structure
        output_dir = get_output_dir(format)
    
    # Find the file
    file_path = output_dir / filename
    if not file_path.exists():
        # Try with just the base name
        matches = list(output_dir.glob(f"*{filename}*"))
        if not matches:
            # If no matches and we're in docs without a source, try searching in all subdirectories
            if format == 'docs' and not source:
                for subdir in ['write', 'research', 'scrape']:
                    subdir_path = get_docs_dir(subdir)
                    submatches = list(subdir_path.glob(f"*{filename}*"))
                    if submatches:
                        matches.extend(submatches)
            
            if not matches:
                click.echo(f"❌ No file found matching '{filename}' in {output_dir}")
                return 1
        file_path = matches[0]
    
    # Read the file content
    content = file_path.read_text(encoding='utf-8')
    
    # Create a rich console
    console = Console()
    
    # If it's a markdown file, render it with rich's markdown support
    if file_path.suffix in ['.md', '.markdown']:
        markdown = Markdown(content)
        console.print(markdown)
        
        # Handle images if enabled
        if show_images:
            # Extract image references
            images = extract_markdown_images(content)
            
            if images:
                # Print a newline first, then the panel
                console.print("")  # Add a blank line before the image section
                console.print(Panel.fit("📷 Images in Document", style="cyan"))
                
                # Process each image
                for i, img in enumerate(images):
                    console.print(f"\n[bold cyan]Image {i+1}:[/bold cyan] {img['alt']}")
                    
                    # Use image width from markdown if available, otherwise use the default
                    display_width = img['width'] or image_width
                    display_height = img['height'] or None
                    
                    # Check if URL is a web URL or file path
                    url = img['url']
                    if url.startswith(('http://', 'https://')):
                        # For web URLs, display the URL
                        console.print(f"[dim]URL: {url}[/dim]")
                        
                        # Try to download and display all remote images
                        try:
                            # Create a temporary file for the image
                            import tempfile
                            import requests
                            from urllib.parse import urlparse
                            
                            # Get the file extension from the URL or default to .jpg
                            parsed_url = urlparse(url)
                            path = parsed_url.path.lower()
                            if path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                                # Use the correct extension
                                ext = os.path.splitext(path)[1]
                            else:
                                # Default to .jpg for unknown types
                                ext = '.jpg'
                            
                            console.print("[dim]Downloading image...[/dim]")
                            
                            # Download the image to a temp file
                            response = requests.get(url, stream=True, timeout=5)
                            response.raise_for_status()
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                                for chunk in response.iter_content(chunk_size=8192):
                                    temp_file.write(chunk)
                                temp_path = temp_file.name
                            
                            # Display the image with dimensions from markdown if specified
                            console.print("[dim]Displaying image...[/dim]")
                            view_image(temp_path, width=display_width, height=display_height)
                            
                            # Delete the temp file after viewing
                            try:
                                os.unlink(temp_path)
                            except:
                                pass  # Ignore errors on cleanup
                                
                        except requests.exceptions.RequestException as e:
                            console.print(f"[yellow]Could not download image: {str(e)}[/yellow]")
                        except Exception as e:
                            console.print(f"[yellow]Error displaying remote image: {str(e)}[/yellow]")
                    else:
                        # For file paths, try to resolve relative to the markdown file
                        img_path = file_path.parent / url
                        if img_path.exists():
                            # Display the image with dimensions from markdown if specified
                            view_image(str(img_path), width=display_width, height=display_height)
                        else:
                            console.print(f"[yellow]Image file not found: {img_path}[/yellow]")
    else:
        # For other files, just print the content
        console.print(content)
    
    return 0
