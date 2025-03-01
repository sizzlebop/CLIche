"""
Image command for CLIche.
Allows searching, downloading, and generating images.
"""
import click
import os
import sys
import time
import subprocess
import base64
import shutil
import importlib.util
from pathlib import Path
from typing import Optional, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.padding import Padding
from ..core import cli
from ..utils.unsplash import UnsplashAPI, get_photo_credit
import re

# Initialize console for rich output
console = Console()

# Global flag to track if we've already checked for dependencies
_viewing_deps_checked = False

# Try to import PIL for image size detection
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def get_image_dimensions(image_path: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Get the dimensions of an image using PIL if available.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (width, height) or (None, None) if PIL is not available
        or there was an error getting the dimensions
    """
    if not HAS_PIL:
        return None, None
    
    try:
        with Image.open(image_path) as img:
            return img.width, img.height
    except Exception:
        return None, None

def calculate_display_dimensions(
    actual_width: Optional[int], 
    actual_height: Optional[int],
    requested_width: Optional[int] = None, 
    requested_height: Optional[int] = None
) -> Tuple[int, int]:
    """
    Calculate appropriate display dimensions for terminal viewing.
    
    Args:
        actual_width: Actual width of the image, if known
        actual_height: Actual height of the image, if known
        requested_width: User-requested width, if any
        requested_height: User-requested height, if any
        
    Returns:
        Tuple of (display_width, display_height) suitable for terminal display
    """
    # Default terminal-friendly dimensions
    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 45  # Slightly taller default for better portrait viewing
    MAX_WIDTH = 120  # Maximum width for reasonable terminal display
    
    # Case 1: Both requested dimensions provided - use them directly
    if requested_width and requested_height:
        return requested_width, requested_height
        
    # Case 2: Image dimensions available
    if actual_width and actual_height:
        # Calculate aspect ratio
        aspect_ratio = actual_width / actual_height
        
        # Case 2.1: Only requested width provided
        if requested_width and not requested_height:
            # Calculate height based on aspect ratio
            height = int(requested_width / aspect_ratio)
            # Ensure minimum height for visibility
            return requested_width, max(height, 20)
            
        # Case 2.2: Only requested height provided
        elif requested_height and not requested_width:
            # Calculate width based on aspect ratio
            width = int(requested_height * aspect_ratio)
            # Cap width to maximum for terminal
            return min(width, MAX_WIDTH), requested_height
            
        # Case 2.3: No requested dimensions
        else:
            # For small images (icons, etc), preserve their small size in terminal
            if actual_width <= MAX_WIDTH // 2 and actual_height <= DEFAULT_HEIGHT // 2:
                # For very small images, use their actual pixel dimensions as terminal characters
                # This makes small images appear at a reasonable size
                return actual_width, actual_height
            
            # For larger images, scale to fit terminal based on image orientation
            if aspect_ratio > 2.5:  # Very wide image
                display_width = min(DEFAULT_WIDTH, MAX_WIDTH)
                display_height = max(int(display_width / aspect_ratio), 15)
            elif aspect_ratio < 0.6:  # Portrait orientation (like DALL-E 1024x1792)
                # For portrait images, use a taller display height
                display_height = min(DEFAULT_HEIGHT * 1.5, 70)  # Taller but with a cap
                display_width = int(display_height * aspect_ratio)
            else:  # Normal proportions
                # Start with default width, calculate height
                display_width = DEFAULT_WIDTH
                display_height = int(display_width / aspect_ratio)
                
                # If height is too tall for terminal, adjust both
                if display_height > DEFAULT_HEIGHT * 1.5:
                    display_height = DEFAULT_HEIGHT
                    display_width = int(display_height * aspect_ratio)
            
            return display_width, display_height
    
    # Case 3: Only requested width provided, no image dimensions
    if requested_width and not requested_height:
        # For just width, use a taller height to accommodate portrait images
        return requested_width, DEFAULT_HEIGHT
        
    # Case 4: Only requested height provided, no image dimensions
    if requested_height and not requested_width:
        return DEFAULT_WIDTH, requested_height
        
    # Case 5: No dimensions provided at all
    return DEFAULT_WIDTH, DEFAULT_HEIGHT

def check_sixel_support() -> bool:
    """Check if the terminal supports SIXEL graphics."""
    # Check for known SIXEL-capable terminals
    term = os.environ.get("TERM", "").lower()
    if "sixel" in term:
        return True
        
    # Check for xterm with SIXEL support
    if term.startswith("xterm") and os.environ.get("XTERM_VERSION"):
        try:
            # Try to query terminal for sixel support using DECRQSS
            sys.stdout.write("\033P+q\"q\033\\")
            sys.stdout.flush()
            # A proper response would indicate SIXEL support
            # This is a simplification and might not work in all terminals
            return True
        except:
            pass
            
    return False

def open_with_default_viewer(path: Path) -> bool:
    """Open the image with the default system viewer."""
    try:
        # Detect OS and use appropriate command
        if sys.platform.startswith('darwin'):  # macOS
            subprocess.run(['open', str(path)], check=False)
        elif sys.platform.startswith('win'):  # Windows
            os.startfile(str(path))
        else:  # Linux and others
            subprocess.run(['xdg-open', str(path)], check=False)
            
        console.print("[green]Opened image with default system viewer.[/green]")
        return True
    except Exception as e:
        console.print(f"[yellow]Could not open with default viewer: {str(e)}[/yellow]")
        return False

def check_terminal_colors():
    """Check how many colors the terminal supports."""
    term = os.environ.get("TERM", "").lower()
    
    # Check for known high-color terminals
    if "256color" in term or "24bit" in term or "truecolor" in term:
        return 256
    
    # Check for known limited color terminals
    if "16color" in term:
        return 16
    
    # Default to 8 colors for safety
    return 8

def view_image(image_path: str, width: Optional[int] = None, height: Optional[int] = None) -> bool:
    """
    View an image in the terminal using the best available method.
    
    Args:
        image_path: Path to the image file
        width: Optional width to resize the image to
        height: Optional height to resize the image to
        
    Returns:
        True if image was displayed successfully, False otherwise
    """
    try:
        # Convert to Path object and resolve to absolute path
        path = Path(os.path.expanduser(image_path)).resolve()
        
        # Check if file exists
        if not path.exists():
            console.print(f"[bold red]Error:[/bold red] Image file not found: {path}")
            return False
        
        # Get actual image dimensions if possible
        actual_width, actual_height = get_image_dimensions(str(path))
        
        # Check if this is likely a Stability AI image (most have 1:1 aspect ratio)
        is_stability_image = False
        if actual_width and actual_height:
            aspect_ratio = actual_width / actual_height
            # If it's a square image (or very close to square), it's likely from Stability
            if 0.95 <= aspect_ratio <= 1.05:
                is_stability_image = True
                # If no width specified and it's a square image, use a wider default width
                # and shorter height to compensate for terminal character aspect ratio
                if width is None:
                    width = 120  # Use maximum width for square images
                if height is None:
                    # Use a shorter height to compensate for terminal character cells being taller than wide
                    height = 50   # This helps square images look more square
        
        # Calculate display dimensions based on actual and requested dimensions
        display_width, display_height = calculate_display_dimensions(
            actual_width, actual_height, width, height
        )
        
        # Always inform where the image is located
        console.print(f"[bold cyan]Image location:[/bold cyan] {path}")
        
        # Track if we successfully viewed in terminal
        viewed_in_terminal = False
        
        # Try terminal viewers in order of preference
        
        # 1. Try Kitty's icat if available (best quality)
        if shutil.which("kitty") and "KITTY_WINDOW_ID" in os.environ:
            try:
                subprocess.run(["kitty", "+kitten", "icat", str(path)], check=True, stderr=subprocess.DEVNULL)
                viewed_in_terminal = True
                return True
            except:
                pass
        
        # 2. Try iTerm2's imgcat protocol if we're in iTerm
        if not viewed_in_terminal and "ITERM_SESSION_ID" in os.environ:
            try:
                with open(path, "rb") as image_file:
                    image_data = image_file.read()
                    b64_data = base64.b64encode(image_data).decode("ascii")
                    sys.stdout.write(f"\033]1337;File=inline=1:{b64_data}\a")
                    sys.stdout.flush()
                viewed_in_terminal = True
                return True
            except:
                pass
        
        # 3. Try chafa terminal viewer if available
        if not viewed_in_terminal and shutil.which("chafa"):
            try:
                # Detect terminal color support
                color_depth = check_terminal_colors()
                
                # Check chafa version to determine available features
                chafa_version = None
                try:
                    version_output = subprocess.check_output(["chafa", "--version"], 
                                                          stderr=subprocess.STDOUT,
                                                          universal_newlines=True)
                    # Parse version from output like "chafa 1.8.0"
                    version_match = re.search(r'chafa (\d+)\.(\d+)\.(\d+)', version_output)
                    if version_match:
                        major = int(version_match.group(1))
                        minor = int(version_match.group(2))
                        patch = int(version_match.group(3))
                        chafa_version = (major, minor, patch)
                except:
                    # If we can't get the version, assume an older version
                    chafa_version = (0, 0, 0)
                
                # Build the chafa command with appropriate options
                chafa_cmd = ["chafa", 
                           "--dither", "ordered",  # Add dithering for better image quality
                           "--symbols", "block+border+space+extra",  # Use a wide range of symbols for higher quality
                           "--color-space", "rgb",  # Use RGB color space for more accurate colors
                           "--colors", str(color_depth)]
                
                # For square images (likely from Stability), use special settings
                if is_stability_image:
                    # Don't clear screen for square images to prevent visual confusion
                    pass
                else:
                    # For non-square images, clear the screen
                    chafa_cmd.append("--clear")
                
                # Add size option with calculated dimensions
                chafa_cmd.extend(["--size", f"{display_width}x{display_height}"])
                
                # Check if we can use pixel aspect ratio adjustment (chafa 1.10.0+)
                supports_pixel_aspect = False
                if chafa_version and chafa_version[0] >= 1 and chafa_version[1] >= 10:
                    supports_pixel_aspect = True
                
                # For square images, apply special handling for better display
                if is_stability_image and supports_pixel_aspect:
                    # If chafa supports pixel-aspect, use it to make square images look square
                    chafa_cmd.extend(["--pixel-aspect", "0.5"])  # Terminal chars are about half as wide as they are tall
                
                # Add the image path
                chafa_cmd.append(str(path))
                
                # Run chafa with the constructed command
                subprocess.run(chafa_cmd, check=True)
                viewed_in_terminal = True
                
                return True
            except Exception:
                pass
        
        # If we get here, we couldn't view in terminal
        if not viewed_in_terminal:
            if not shutil.which("chafa"):
                console.print("[yellow]Terminal viewing requires chafa. Run:[/yellow] cliche image --install-deps")
            else:
                console.print("[yellow]Terminal viewing failed.[/yellow]")
                
            console.print(f"[cyan]Try opening with system viewer:[/cyan] cliche image --system-view {path}")
            
            # Ask if user wants to open with system viewer
            if shutil.which("xdg-open") and sys.platform == "linux":
                choice = input("\nOpen with system viewer? (y/n): ").strip().lower()
                if choice.startswith('y'):
                    subprocess.run(['xdg-open', str(path)], check=False)
                    return True
        
        return viewed_in_terminal
        
    except Exception as e:
        console.print(f"[bold red]Error viewing image:[/bold red] {str(e)}")
        return False

def check_viewing_dependencies(silent=True):
    """
    Check for image viewing dependencies and suggest installation if missing.
    
    If silent is True, no message will be displayed, only environment setup is done.
    Returns a tuple (has_chafa, has_fallback) indicating if viewing tools are available.
    """
    global _viewing_deps_checked
    
    # Skip if already checked
    if _viewing_deps_checked:
        return
        
    # Check for Pillow
    try:
        importlib.util.find_spec('PIL')
    except ImportError:
        if not silent:
            console.print("[yellow]Warning: Pillow not installed. Image viewing may not work properly.[/yellow]")
            console.print("Run: pip install Pillow")
        return False, False
    
    # Check for chafa (our primary character-based viewer)
    has_chafa = shutil.which("chafa") is not None
    
    # Check for any fallback viewers
    has_kitty = "KITTY_WINDOW_ID" in os.environ
    has_iterm = "ITERM_SESSION_ID" in os.environ
    has_sixel = check_sixel_support() and shutil.which("img2sixel") is not None
    
    has_fallback = has_kitty or has_iterm or has_sixel
    
    # Mark as checked
    _viewing_deps_checked = True
    
    return has_chafa, has_fallback

def install_viewer_dependencies():
    """
    Check for and install image viewing dependencies if missing.
    Returns True if dependencies are available or installed successfully.
    """
    # Check if our primary viewer (chafa) is available
    if shutil.which("chafa"):
        console.print("[green]Chafa is already installed.[/green]")
        return True
    
    # First try with pip to install Python dependencies
    try:
        console.print("[yellow]Installing Python image dependencies...[/yellow]")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "Pillow", "python-magic"], check=False)
    except:
        pass
        
    # Try to detect the platform and package manager
    if shutil.which("apt-get"):  # Debian/Ubuntu
        console.print("[yellow]Installing chafa for terminal image viewing...[/yellow]")
        try:
            # Check if we have sudo permissions
            sudo_test = subprocess.run(["sudo", "-n", "true"], 
                                      stdout=subprocess.DEVNULL, 
                                      stderr=subprocess.DEVNULL, 
                                      check=False)
            
            if sudo_test.returncode == 0:
                # We have passwordless sudo access
                subprocess.run(["sudo", "apt-get", "install", "-y", "chafa"], check=False)
                if shutil.which("chafa"):
                    console.print("[green]Successfully installed chafa![/green]")
                    return True
            else:
                console.print("[yellow]Please run:[/yellow] sudo apt-get install -y chafa")
        except:
            console.print("[yellow]Please run:[/yellow] sudo apt-get install -y chafa")
    
    elif shutil.which("brew"):  # macOS with Homebrew
        console.print("[yellow]Installing chafa for terminal image viewing...[/yellow]")
        try:
            subprocess.run(["brew", "install", "chafa"], check=False)
            if shutil.which("chafa"):
                console.print("[green]Successfully installed chafa![/green]")
                return True
        except:
            console.print("[yellow]Please run:[/yellow] brew install chafa")
    
    elif shutil.which("dnf"):  # Fedora/RHEL
        console.print("[yellow]Installing chafa for terminal image viewing...[/yellow]")
        try:
            sudo_test = subprocess.run(["sudo", "-n", "true"], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL, 
                                     check=False)
            if sudo_test.returncode == 0:
                subprocess.run(["sudo", "dnf", "install", "-y", "chafa"], check=False)
                if shutil.which("chafa"):
                    console.print("[green]Successfully installed chafa![/green]")
                    return True
            else:
                console.print("[yellow]Please run:[/yellow] sudo dnf install -y chafa")
        except:
            console.print("[yellow]Please run:[/yellow] sudo dnf install -y chafa")
            
    # Check if installation was successful
    if shutil.which("chafa"):
        return True
    
    # If we get here, we couldn't install automatically
    console.print("[yellow]Please install chafa manually for the best image viewing experience.[/yellow]")
    console.print("  - Ubuntu/Debian: sudo apt install chafa")
    console.print("  - macOS: brew install chafa")
    console.print("  - Fedora/RHEL: sudo dnf install chafa")
    
    return False

# Check for dependencies when module is imported - do this after all function definitions
check_viewing_dependencies(silent=True)

@cli.command()
@click.argument('query', nargs=-1, required=False)
@click.option('--generate', '-g', is_flag=True, help='Generate an image')
@click.option('--provider', '-p', help='Specify the image generation provider (e.g., dalle, stability)')
@click.option('--model', '-m', help='Specify the model for image generation')
@click.option('--size', '-s', default="1024x1024", help='Specify image size (e.g., 1024x1024)')
@click.option('--quality', '-q', type=click.Choice(['standard', 'hd']), default='standard', help='Specify image quality (e.g., standard, hd)')
@click.option('--style', help='Specify image style (e.g., vivid, natural)')
@click.option('--list', '-l', is_flag=True, help='List images matching the query')
@click.option('--download', '-d', help='Download an image by URL or identifier')
@click.option('--view', '-v', help='View an image file in the terminal (uses chafa if available)')
@click.option('--system-view', '-sv', help='Open an image with your system\'s default viewer')
@click.option('--width', '-w', type=int, help='Width for display in characters (auto-scales if only width provided)')
@click.option('--height', '-h', type=int, help='Height for display in characters (auto-scales if only height provided)')
@click.option('--count', '-c', type=int, default=10, help='Number of results to show (default: 10)')
@click.option('--page', '-p', type=int, default=1, help='Results page (default: 1)')
@click.option('--list-providers', is_flag=True, help='List available image generation providers')
@click.option('--list-models', is_flag=True, help='List available models for a provider')
@click.option('--list-styles', is_flag=True, help='List available style options for a provider')
@click.option('--list-all', is_flag=True, help='List all available providers and models')
@click.option('--search', help='Search for images - same as passing query with --list')
@click.option('--auto-view', is_flag=True, help='[DEPRECATED] Use --view instead for terminal viewing')
@click.option('--install-deps', is_flag=True, help='Install terminal image viewing dependencies')
def image(query, generate, provider, model, size, quality, style, list, download, view, 
          system_view, width, height, count, page, list_providers, list_models, list_styles, 
          list_all, search, auto_view, install_deps):
    """Image generation and handling command.
    
    This command provides functionality for:
    
    - Generating images with AI services (OpenAI DALL-E, etc.)
    - Viewing images in the terminal (with chafa)
    - Opening images with system viewers
    - Downloading images from the web
    - Listing available image providers and models
    
    INTELLIGENT IMAGE SIZING:
    
    When viewing images in the terminal, the command uses intelligent sizing to:
    
    - Automatically detect actual image dimensions when possible
    - Preserve aspect ratio when only width or height is specified
    - Use appropriate terminal-friendly dimensions for different image types
    - Make small images (icons, etc.) appear at a reasonable size
    - Provide information about the original and display dimensions
    
    Examples:
    
    # Generate an image
    cliche image -g "A serene mountain landscape at sunset"
    
    # Generate with specific provider and model
    cliche image -g "A futuristic city" -p openai -m dall-e-3
    
    # View an image in the terminal
    cliche image --view path/to/image.jpg
    
    # View with custom width (height auto-calculated)
    cliche image --view path/to/image.jpg --width 120
    
    # Open with system viewer
    cliche image --system-view path/to/image.jpg
    
    # List available providers
    cliche image --list-providers
    
    # Install dependencies for terminal viewing
    cliche image --install-deps
    """
    # Check if we need to install dependencies
    if install_deps:
        if install_viewer_dependencies():
            console.print("[bold green]Terminal image viewing dependencies installed successfully![/bold green]")
            console.print("You can now view images directly in your terminal with: cliche image --view PATH_TO_IMAGE")
        else:
            console.print("[bold yellow]For in-terminal image viewing, please install chafa:[/bold yellow]")
            console.print("  - Ubuntu/Debian: sudo apt-get install chafa")
            console.print("  - macOS: brew install chafa")
        return
    
    # Warn if auto-view is used, but don't enable it
    if auto_view:
        console.print("[bold yellow]Note:[/bold yellow] The --auto-view option is deprecated.")
        console.print("Terminal viewing is now enabled by default with: cliche image --view PATH_TO_IMAGE")
    
    # Handle information listing options first
    if list_providers:
        show_providers()
        return
    
    if list_models:
        show_models(provider)
        return
    
    if list_styles:
        show_styles(provider)
        return
    
    if list_all:
        # Show providers first
        show_providers()
        console.print("\n")
        
        # Then show models for each provider
        from ..utils.image_generation import ImageGenerator
        generator = ImageGenerator()
        providers = [p.get('id') for p in generator.list_providers()]
        
        for provider_id in providers:
            console.print(f"\n[bold cyan]Models for {provider_id.capitalize()}:[/bold cyan]")
            show_models(provider_id)
        
        return
    
    # Handle direct system viewer opening
    if system_view:
        path = Path(os.path.expanduser(system_view)).resolve()
        if not path.exists():
            console.print(f"[bold red]Error:[/bold red] Image file not found: {path}")
            return False
            
        console.print(f"[bold cyan]Opening image with system viewer:[/bold cyan] {path}")
        open_with_default_viewer(path)
        return
    
    # Handle image viewing - use wider default width for terminal viewing, but maintain image proportions
    if view:
        # Try to get image dimensions first to determine appropriate default width
        try:
            actual_width, actual_height = get_image_dimensions(view)
            if actual_width and actual_height:
                aspect_ratio = actual_width / actual_height
                
                # Special handling for square images (likely from Stability AI)
                if 0.95 <= aspect_ratio <= 1.05:
                    # Square images need special handling for terminal display
                    if not width and not height:
                        # No dimensions specified - use optimal defaults for square images
                        view_width = 120
                        view_height = 50
                        view_image(view, view_width, view_height)
                        return
                    else:
                        # User specified dimensions - respect those
                        view_width = width
                        view_height = height
                # For portrait images, use narrower default width
                elif aspect_ratio < 0.8 and not width:  # Portrait orientation
                    view_width = 80  # Narrower width works better for portrait images
                else:
                    view_width = width if width is not None else 100
            else:
                view_width = width if width is not None else 100
        except:
            # If can't determine dimensions, use standard default
            view_width = width if width is not None else 100
            
        view_image(view, view_width, height)
        return
    
    # Handle image generation
    if generate:
        # Process the query (prompt)
        prompt = ' '.join(query) if query else None
        
        # Need a query for generation
        if not prompt:
            console.print("[bold red]Error:[/bold red] Please provide a text prompt for image generation")
            console.print("Example: cliche image \"a red fox in a forest\" --generate")
            sys.exit(1)
        
        try:
            image_path = generate_image(prompt, provider, model, size, quality, style)
            
            # Success - the generate_image function already displays viewing instructions
            return image_path
        except Exception as e:
            console.print(f"[bold red]Error generating image:[/bold red] {str(e)}")
            sys.exit(1)
        return
    
    # Handle image download - use larger defaults for download sizes
    if download:
        try:
            # Import the unsplash module
            from ..utils.unsplash import UnsplashAPI
            
            # Initialize the API
            unsplash = UnsplashAPI()
            
            # Set default width/height for downloading if not specified
            download_width = width if width is not None else 1600
            download_height = height if height is not None else 900
            
            # Download the image
            image_path = unsplash.download_photo(download, download_width, download_height)
            
            # Get photo details for credits
            photo_details = unsplash.get_photo(download)
            
            # Show success message with credits
            console.print(f"[bold green]Downloaded image to:[/bold green] {image_path}")
            
            # Show photo credits
            if photo_details:
                user = photo_details.get('user', {})
                name = user.get('name', 'Unknown')
                username = user.get('username', 'unknown')
                
                console.print(f"[bold]Photo by:[/bold] {name} (@{username}) on Unsplash")
            
            # Show viewing instructions
            console.print("\n[bold green]To view this image:[/bold green]")
            console.print(f"  cliche image --view {image_path}")
            console.print(f"  cliche image --system-view {image_path}")
            
            return image_path
        except Exception as e:
            console.print(f"[bold red]Error downloading image:[/bold red] {str(e)}")
            sys.exit(1)
        return
    
    # Handle search functionality
    search_query = None
    
    # If --search option is used, set search_query
    if search:
        search_query = search
        list = True
    # If query is provided with --list flag, use that
    elif query and list:
        search_query = ' '.join(query)
    # If no query provided for listing, show help
    elif list:
        console.print("[bold yellow]Please provide a search query.[/bold yellow]")
        console.print("Example: cliche image nature --list")
        sys.exit(1)
    
    # List images matching search query
    if search_query:
        console.print(f"[bold cyan]Searching Unsplash for:[/bold cyan] {search_query}")
        
        try:
            # Import the unsplash module
            from ..utils.unsplash import UnsplashAPI
            
            # Initialize the API
            unsplash = UnsplashAPI()
            
            # Search for photos
            results = unsplash.search_photos(search_query, page=page, per_page=count)
            total = results.get('total', 0)
            total_pages = (total + count - 1) // count
            
            # Create table for results
            table = Table(title=f"Unsplash Results: {search_query} (Page {page}/{total_pages})")
            table.add_column("ID", style="cyan")
            table.add_column("Description", style="green")
            table.add_column("Author", style="yellow")
            
            # Add results to table
            photos = results.get('results', [])
            for photo in photos:
                # Get ID, description, and author
                photo_id = photo.get('id', 'unknown')
                description = photo.get('description', '') or photo.get('alt_description', '') or 'No description'
                
                # Get author info
                user = photo.get('user', {})
                author = user.get('name', 'Unknown')
                
                # Add row to table
                table.add_row(photo_id, description, author)
            
            # Print table
            console.print(table)
            
            # Show instructions for downloading - use the default download sizes
            download_width = width if width is not None else 1600
            download_height = height if height is not None else 900
            
            console.print("\n[bold]To download an image:[/bold]")
            console.print(f"  cliche image --download IMAGE_ID --width {download_width} --height {download_height}\n")
            
            # Show pagination info if multiple pages
            if total_pages > 1:
                console.print(f"[dim]Showing page {page} of {total_pages}[/dim]")
                if page < total_pages:
                    console.print(f"[dim]For next page:[/dim] cliche image {search_query} --list --page {page+1}")
                if page > 1:
                    console.print(f"[dim]For previous page:[/dim] cliche image {search_query} --list --page {page-1}")
                    
        except Exception as e:
            console.print(f"[bold red]Error searching for images:[/bold red] {str(e)}")
            sys.exit(1)
        return
    
    # If no specific action requested, show help
    click.echo(image.get_help(click.Context(image)))
    sys.exit(0)

def generate_image(prompt: str, provider: Optional[str] = None, model: Optional[str] = None,
                   size: Optional[str] = None, quality: Optional[str] = None, 
                   style: Optional[str] = None) -> Optional[str]:
    """
    Generate an image using the specified provider.
    
    Args:
        prompt: Text prompt for image generation
        provider: Image provider to use (defaults to config setting)
        model: Model to use (provider-specific)
        size: Image size as "widthxheight" (e.g. "1024x1024")
        quality: Image quality (provider-specific)
        style: Style preset (provider-specific)
        
    Returns:
        Path to the generated image if successful, None otherwise
    """
    try:
        # Import image generator
        from ..utils.image_generation import ImageGenerator
        from ..core import Config
        import json
        
        start_time = time.time()
        
        # Load config for defaults
        config = Config().config
        image_config = config.get('image_generation', {})
        default_provider = image_config.get('default_provider', 'dalle')
        default_models = image_config.get('default_models', {})
        
        # Use provider from args or default from config
        used_provider = provider or default_provider
        
        # Initialize generator with the provider
        try:
            generator = ImageGenerator(provider=used_provider)
        except Exception as e:
            console.print(f"[bold red]Error initializing image generator:[/bold red] {str(e)}")
            
            # Check for API key configuration
            if used_provider == 'dalle':
                # Check if DALL-E API key is configured
                if not os.environ.get('OPENAI_API_KEY') and not config.get('services', {}).get('dalle', {}).get('api_key'):
                    console.print("[yellow]DALL-E API key not found! Run:[/yellow] cliche config --dalle-key YOUR_API_KEY")
            elif used_provider == 'stability':
                # Check if Stability API key is configured
                if not os.environ.get('STABILITY_API_KEY') and not config.get('services', {}).get('stability_ai', {}).get('api_key'):
                    console.print("[yellow]Stability API key not found! Run:[/yellow] cliche config --stability-key YOUR_API_KEY")
            
            return None
        
        # Get provider display name
        provider_name = generator.provider_name
        
        # Get the model that will be used (either specified or default)
        used_model = model
        if not used_model:
            # Try to get default model from config
            used_model = default_models.get(used_provider)
            if not used_model:
                # Use provider-specific fallback defaults
                if used_provider.lower() == 'dalle':
                    used_model = 'dall-e-3'
                elif used_provider.lower() == 'stability':
                    used_model = 'stable-diffusion-xl-1024-v1-0'
        
        # Print information about the generation process
        console.print(f"[bold cyan]Generating image with {provider_name}[/bold cyan]")
        console.print(f"[bold]Prompt:[/bold] {prompt}")
        
        console.print("[yellow]Generating image, please wait...[/yellow]")
        
        # Generate the image
        try:
            result = generator.generate_image(
                prompt=prompt,
                model=used_model,
                size=size,
                quality=quality,
                style=style
            )
        except Exception as api_error:
            # Simplified error message
            console.print(f"[bold red]Image generation failed:[/bold red] {str(api_error)}")
            if used_provider.lower() == 'dalle':
                console.print("[yellow]Check your OpenAI API key and available credits.[/yellow]")
            elif used_provider.lower() == 'stability':
                console.print("[yellow]Check your Stability AI API key and available credits.[/yellow]")
            return None
        
        # Calculate generation time
        elapsed_time = time.time() - start_time
        
        # Handle successful generation
        if result and 'image_path' in result:
            image_path = result['image_path']
            
            # Show success message
            console.print(f"[bold green]Image generated successfully![/bold green]")
            console.print(f"[bold]Image saved to:[/bold] {image_path}")
            console.print(f"[dim]Generation time: {elapsed_time:.2f} seconds[/dim]")
            
            # Show revised prompt if it was modified by the service
            if 'revised_prompt' in result and result['revised_prompt'] != prompt:
                console.print(f"\n[bold yellow]Provider revised your prompt to:[/bold yellow]")
                console.print(f"{result['revised_prompt']}")
            
            # Show viewing instructions (still keep these for reference)
            console.print("\n[bold green]Image viewing commands:[/bold green]")
            console.print(f"  cliche image --view {image_path}")
            console.print(f"  cliche image --system-view {image_path}")
            
            # Now automatically view the image in terminal without unnecessary messages
            view_image(image_path)
            
            # Return the path to the generated image
            return str(image_path)
        else:
            # More concise error message when image generation fails
            console.print("[bold red]Error:[/bold red] Failed to generate image")
            console.print("Check your API key and configuration with 'cliche config --help'")
            return None
            
    except ValueError as e:
        # Handle missing API key
        if "API key" in str(e):
            provider_config_option = f"--{used_provider.lower()}-key"
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            console.print(f"[yellow]Run:[/yellow] cliche config {provider_config_option} YOUR_API_KEY")
        else:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return None
        
    except ModuleNotFoundError:
        # Handle missing dependencies
        console.print(f"[bold red]Error:[/bold red] Required module not found")
        console.print("[yellow]Please install required packages with pip[/yellow]")
        return None
        
    except Exception as e:
        # Handle other errors
        console.print(f"[bold red]Error generating image:[/bold red] {str(e)}")
        
        # Provide simple alternative suggestions
        if used_provider.lower() == 'dalle':
            console.print("[yellow]Try using Stability AI instead:[/yellow] --provider stability")
        else:
            console.print("[yellow]Try using DALL-E instead:[/yellow] --provider dalle")
        return None

def show_providers():
    """Show available image generation providers."""
    try:
        from ..utils.image_generation import ImageGenerator
        from ..core import Config
        
        # Get config to check default provider
        config = Config().config
        default_provider = config.get('image_generation', {}).get('default_provider', 'dalle')
        
        # Initialize generator with default provider
        generator = ImageGenerator()
        
        # Get available providers
        providers = generator.list_providers()
        
        # Create table
        table = Table(title="Available Image Generation Providers")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="yellow")
        table.add_column("Default", style="magenta")
        
        for provider in providers:
            provider_id = provider.get('id', 'unknown')
            is_default = '✓' if provider_id == default_provider else ''
            
            table.add_row(
                provider_id,
                provider.get('name', 'Unknown'),
                provider.get('description', ''),
                is_default
            )
        
        console.print(table)
        
        # Show current default provider model if configured
        default_models = config.get('image_generation', {}).get('default_models', {})
        if default_provider in default_models:
            default_model = default_models[default_provider]
            console.print(f"\n[bold cyan]Current default:[/bold cyan] [green]{default_provider}[/green] with model [green]{default_model}[/green]")
        
        # Show usage instructions - simplified
        console.print("\n[bold]Usage:[/bold] cliche image \"your prompt\" --generate --provider PROVIDER_ID")
        console.print("[bold]Configure:[/bold] cliche config --image-provider PROVIDER --image-model MODEL_ID")
        
    except ImportError:
        console.print("[bold red]Error:[/bold red] Image generation utilities not available")
    except Exception as e:
        console.print(f"[bold red]Error listing providers:[/bold red] {str(e)}")

def show_models(provider=None):
    """Show available models for a specific provider or all providers."""
    try:
        from ..utils.image_generation import ImageGenerator, ImageProvider
        from ..core import Config
        
        # Get config to check defaults
        config = Config().config
        image_config = config.get('image_generation', {})
        default_provider = image_config.get('default_provider', 'dalle')
        default_models = image_config.get('default_models', {})
        
        # If no provider specified, use default
        if not provider:
            provider = default_provider
            console.print(f"[yellow]Using default provider: [bold]{provider}[/bold][/yellow]\n")
        
        # Initialize generator with the specified provider
        generator = ImageGenerator(provider=provider)
        
        # Get models for the provider
        models = generator.list_models()
        
        # Get default model for this provider
        current_default_model = default_models.get(provider)
        if not current_default_model:
            current_default_model = generator.get_default_model(provider)
        
        # Create table
        table = Table(title=f"Available Models for {provider.capitalize()}")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="yellow")
        table.add_column("Default", style="magenta")
        
        # Count different model sources
        api_models_count = 0
        extended_models_count = 0
        
        for model in models:
            model_id = model.get('id', 'unknown')
            is_default = '✓' if model_id == current_default_model else ''
            
            # Track if this is an API model by description
            if "API-provided model" in model.get('description', ''):
                api_models_count += 1
                # Mark API-provided models with a different style
                table.add_row(
                    f"[bold]{model_id}[/bold]",
                    model.get('name', 'Unknown'),
                    model.get('description', ''),
                    is_default
                )
            else:
                extended_models_count += 1
                table.add_row(
                    model_id,
                    model.get('name', 'Unknown'),
                    model.get('description', ''),
                    is_default
                )
        
        console.print(table)
        
        # Show brief provider-specific notes
        if provider.lower() == 'stability':
            console.print("\n[yellow]Note:[/yellow] Bold entries are models directly available through the API.")
        
        # Simplified usage instructions
        console.print(f"\n[bold]Usage:[/bold] cliche image \"prompt\" --generate --provider {provider} --model MODEL_ID")
        console.print(f"[bold]Configure:[/bold] cliche config --image-provider {provider} --image-model MODEL_ID")
        
    except ImportError:
        console.print("[bold red]Error:[/bold red] Image generation utilities not available")
    except Exception as e:
        console.print(f"[bold red]Error listing models:[/bold red] {str(e)}")

def show_styles(provider=None):
    """Show available style options for a specific provider."""
    try:
        from ..utils.image_generation import ImageGenerator
        from ..core import Config
        
        # Get config to check defaults
        config = Config().config
        default_provider = config.get('image_generation', {}).get('default_provider', 'dalle')
        
        # If no provider specified, use default
        if not provider:
            provider = default_provider
            console.print(f"[yellow]Using default provider: [bold]{provider}[/bold][/yellow]\n")
        
        # Create table
        table = Table(title=f"Available Style Options for {provider.capitalize()}")
        table.add_column("Style", style="cyan")
        table.add_column("Description", style="green")
        
        # Provider-specific style options
        if provider.lower() == 'dalle':
            table.add_row("vivid", "Vibrant, bright, and more saturated. Good for bold, dramatic imagery.")
            table.add_row("natural", "More true-to-life and less exaggerated. Good for realistic imagery.")
            console.print(table)
            
            console.print("\n[yellow]Note:[/yellow] DALL-E 3 supports 'vivid' and 'natural' styles.")
            
        elif provider.lower() == 'stability':
            table.add_row("enhance", "Default option that enhances your prompt for better image quality")
            table.add_row("anime", "Anime and manga style illustrations")
            table.add_row("photographic", "Realistic, photograph-like images")
            table.add_row("digital-art", "Digital art style with bold colors and sharp details")
            table.add_row("comic-book", "Comic book illustration style")
            table.add_row("fantasy-art", "Fantasy art with magical and mythical elements")
            table.add_row("line-art", "Simple line drawings")
            table.add_row("analog-film", "Analog film photography aesthetic")
            table.add_row("neon-punk", "Cyberpunk style with neon colors")
            table.add_row("isometric", "Isometric 3D style")
            console.print(table)
            
            console.print("\n[yellow]Note:[/yellow] Style support varies by model.")
        else:
            console.print(f"[bold red]Error:[/bold red] No style information available for provider '{provider}'")
            return
        
        # Show usage instructions
        console.print(f"\n[bold]Usage:[/bold] cliche image \"prompt\" --generate --provider {provider} --style STYLE_NAME")
        
    except ImportError:
        console.print("[bold red]Error:[/bold red] Image generation utilities not available")
    except Exception as e:
        console.print(f"[bold red]Error listing styles:[/bold red] {str(e)}") 