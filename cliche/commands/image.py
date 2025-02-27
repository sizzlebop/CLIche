"""
Image command for CLIche.
Allows searching and downloading images from Unsplash.
"""
import click
import os
import sys
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from ..core import cli
from ..utils.unsplash import UnsplashAPI, get_photo_credit

# Initialize console for rich output
console = Console()

@cli.command()
@click.argument('query', nargs=-1, required=False)
@click.option('--list', '-l', is_flag=True, help='List images matching the query')
@click.option('--download', '-d', help='Download image by ID')
@click.option('--width', '-w', type=int, default=1600, help='Download width (default: 1600)')
@click.option('--height', '-h', type=int, default=900, help='Download height (default: 900)')
@click.option('--count', '-c', type=int, default=10, help='Number of results to show (default: 10)')
@click.option('--page', '-p', type=int, default=1, help='Results page (default: 1)')
def image(query: tuple[str, ...], list: bool, download: Optional[str], 
          width: int, height: int, count: int, page: int):
    """Search and download images from Unsplash.
    
    Examples:
        cliche image nature --list      # List nature images
        cliche image mountain lake --list -c 20   # List 20 mountain lake images
        cliche image --download abc123  # Download image with ID abc123
        cliche image sunset --list --page 2 # Show second page of results
        cliche image --download abc123 --width 800 --height 600  # Custom size
    """
    # Initialize Unsplash API client
    try:
        unsplash = UnsplashAPI()
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        console.print("[yellow]Run:[/yellow] cliche config --unsplash-key YOUR_API_KEY")
        sys.exit(1)
    
    # Download a specific image
    if download:
        try:
            # Show download message
            console.print(f"[bold cyan]Downloading image:[/bold cyan] {download}")
            
            # Download the image
            image_path = unsplash.download_photo(download, width, height)
            
            # Get photo details for credits
            photo_data = unsplash.get_photo(download)
            credit = get_photo_credit(photo_data)
            
            # Show success message
            console.print(f"[bold green]Image downloaded to:[/bold green] {image_path}")
            console.print(f"[bold yellow]Photo Credit:[/bold yellow] {credit}")
            console.print("\n[dim]Remember to include proper attribution when using this image.[/dim]")
            
        except Exception as e:
            console.print(f"[bold red]Error downloading image:[/bold red] {str(e)}")
            sys.exit(1)
        return
    
    # If no query provided for listing, show help
    if (not query or len(query) == 0) and list:
        console.print("[bold yellow]Please provide a search query.[/bold yellow]")
        console.print("Example: cliche image nature --list")
        sys.exit(1)
    
    # List images matching query
    if query and list:
        # Join query parts
        search_query = ' '.join(query)
        
        console.print(f"[bold cyan]Searching Unsplash for:[/bold cyan] {search_query}")
        
        try:
            # Search for photos
            results = unsplash.search_photos(search_query, page=page, per_page=count)
            total = results.get('total', 0)
            total_pages = (total + count - 1) // count
            
            # Create table for results
            table = Table(title=f"Unsplash Results: {search_query} (Page {page}/{total_pages})")
            table.add_column("ID", style="cyan")
            table.add_column("Description", style="green")
            table.add_column("Photographer", style="yellow")
            table.add_column("Dimensions", style="blue")
            
            # Add rows to the table
            photos = results.get('results', [])
            if not photos:
                console.print("[bold yellow]No images found for this query.[/bold yellow]")
                sys.exit(0)
                
            for photo in photos:
                photo_id = photo.get('id', 'N/A')
                desc = photo.get('description') or photo.get('alt_description') or 'No description'
                # Truncate description if too long
                if desc and len(desc) > 40:
                    desc = desc[:37] + '...'
                    
                photographer = photo.get('user', {}).get('name', 'Unknown')
                width = photo.get('width', 0)
                height = photo.get('height', 0)
                
                table.add_row(
                    photo_id,
                    desc,
                    photographer,
                    f"{width}x{height}"
                )
            
            # Display the table
            console.print(table)
            
            # Show instructions for downloading
            console.print("\n[bold]To download an image:[/bold]")
            console.print(f"  cliche image --download IMAGE_ID --width {width} --height {height}\n")
            
            # Show pagination info if multiple pages
            if total_pages > 1:
                console.print(f"[dim]Showing page {page} of {total_pages}[/dim]")
                if page < total_pages:
                    console.print(f"[dim]For next page:[/dim] cliche image {search_query} --list --page {page+1}")
                if page > 1:
                    console.print(f"[dim]For previous page:[/dim] cliche image {search_query} --list --page {page-1}")
                    
        except Exception as e:
            console.print(f"[bold red]Error searching images:[/bold red] {str(e)}")
            sys.exit(1)
        return
    
    # If we got here, show the help text
    ctx = click.get_current_context()
    console.print(ctx.get_help()) 