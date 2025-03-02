"""
Command for scraping web content.
"""
import os
import asyncio
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any
import click
from rich.console import Console

from ..scraping.crawl_manager import CrawlManager
from ..scraping.models.data_models import CrawlerConfig, ExtractionResult
from ..core import get_llm

# Configure logger
logger = logging.getLogger(__name__)
console = Console()

def handle_scrape_command(
    url: str,
    output: Optional[str] = None,
    images: bool = False,
    depth: int = 0,
    max_pages: int = 1,
    topic: Optional[str] = None,
    llm: Optional[str] = None,
    raw: bool = False,
    save_json: bool = True,
    verbose: bool = False,
):
    """
    Scrape content from a website and save as JSON.
    
    Args:
        url: URL to scrape
        output: Output JSON file path (optional)
        images: Whether to extract images
        depth: Crawling depth
        max_pages: Maximum number of pages to crawl
        topic: Topic for categorizing and filtering content
        llm: LLM provider to use for content enhancement
        raw: Return raw HTML instead of extracted content
        save_json: Save raw scraped data as JSON
        verbose: Show verbose output
    """
    if verbose:
        # Configure logging to show more details
        logger.setLevel(logging.DEBUG)
        console.print("[bold green]Verbose mode enabled[/bold green]")
    
    # Get output directory
    scrape_dir = Path(os.path.expanduser("~/cliche/files/scrape"))
    scrape_dir.mkdir(parents=True, exist_ok=True)
    
    image_dir = None
    if images:
        image_dir = Path(os.path.expanduser("~/cliche/files/images/scraped"))
        image_dir.mkdir(parents=True, exist_ok=True)
        if topic:
            # Create a subdirectory for this topic
            topic_slug = re.sub(r'[^\w\-]', '_', topic)
            image_dir = image_dir / topic_slug
            image_dir.mkdir(exist_ok=True)
    
    # Create crawler config
    config = CrawlerConfig(
        max_depth=depth,
        max_pages=max_pages,
        max_concurrent=5,
        follow_links=depth > 0,
        same_domain_only=True,
        topic=topic
    )
    
    # Initialize crawl manager
    crawl_manager = CrawlManager()
    
    # Set up LLM if specified
    llm_provider = None
    if llm:
        try:
            llm_provider = get_llm(provider=llm)
            crawl_manager.set_llm(llm_provider)
            console.print(f"[green]Using LLM provider: {llm}[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not initialize LLM provider {llm}: {str(e)}[/yellow]")
    
    console.print(f"[bold blue]Scraping content from {url}[/bold blue]")
    console.print(f"Depth: {depth}, Max pages: {max_pages}, Images: {images}")
    
    try:
        # Run the crawl and extract process
        results = asyncio.run(crawl_manager.crawl_and_extract(
            url=url,
            config=config,
            include_images=images,
            output_dir=image_dir,
            topic=topic
        ))
        
        # Process results
        if not results:
            console.print("[bold red]Error: Failed to extract content[/bold red]")
            return
        
        console.print(f"[green]Successfully extracted content from {len(results)} pages[/green]")
        
        # Add details about the content length for each result
        for i, result in enumerate(results):
            if result.success and result.data:
                content_length = len(result.data.main_content)
                console.print(f"  Page {i+1}: [cyan]{content_length}[/cyan] characters of content")
                if result.data.images:
                    console.print(f"  Page {i+1}: [cyan]{len(result.data.images)}[/cyan] images")
        
        # Prepare data for saving/processing
        extracted_data = []
        
        for result in results:
            if result.success and result.data:
                # Convert image models to dictionaries
                images_list = []
                if result.data.images:
                    for img in result.data.images:
                        if isinstance(img, dict):
                            images_list.append(img)
                        else:
                            # Convert model to dict if needed
                            img_dict = {
                                'url': img.url,
                                'alt_text': img.alt_text,
                                'caption': img.caption,
                                'width': img.width,
                                'height': img.height,
                                'position_index': img.position_index,
                                'source_url': img.source_url,
                                'local_path': img.local_path,
                                'file_type': img.file_type
                            }
                            images_list.append(img_dict)
                
                # Add to extracted data
                extracted_data.append({
                    "url": result.data.url,
                    "title": result.data.title,
                    "description": result.data.description,
                    "main_content": result.data.main_content,
                    "images": images_list,
                    "metadata": result.data.metadata,
                    "timestamp": result.data.timestamp.isoformat() if result.data.timestamp else None
                })
        
        # Save raw data as JSON
        if save_json:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain = urlparse(url).netloc.replace(".", "_")
            topic_slug = f"_{re.sub(r'[^\w\-]', '_', topic)}" if topic else ""
            
            # Use output path if provided, otherwise generate a filename
            if output:
                json_path = Path(output)
            else:
                json_filename = f"scraped_{domain}{topic_slug}_{timestamp}.json"
                json_path = scrape_dir / json_filename
            
            with open(json_path, "w") as f:
                json.dump(extracted_data, f, indent=2)
            
            console.print(f"[green]Saved content to {json_path}[/green]")
            console.print("[yellow]Use 'cliche generate' to create a document from this data[/yellow]")
        
        return extracted_data
            
    except Exception as e:
        console.print(f"[bold red]Error during scraping: {str(e)}[/bold red]")
        logger.exception("Scraping error")
        return None

@click.command()
@click.argument("url")
@click.option("--output", "-o", help="Output JSON file path")
@click.option("--images", "-i", is_flag=True, help="Extract images")
@click.option("--depth", "-d", default=0, help="Crawling depth")
@click.option("--max-pages", "-m", default=3, help="Maximum number of pages to crawl")
@click.option("--topic", "-t", help="Topic for categorizing and filtering content")
@click.option("--llm", help="LLM provider to use for content enhancement")
@click.option("--no-llm", is_flag=True, help="Disable LLM extraction (faster, simpler)")
@click.option("--raw", is_flag=True, help="Return raw HTML instead of extracted content")
@click.option("--save-json", is_flag=True, default=True, help="Save raw scraped data as JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def scrape(
    url, output, images, depth, max_pages, topic, llm, no_llm, raw, save_json, verbose
):
    """Scrape content from a website and save as JSON.
    
    Extracts content from the specified URL and saves it as structured JSON data.
    To generate a document from the scraped data, use the 'generate' command.
    
    Examples:
        cliche scrape https://example.com --topic "Machine Learning"
        cliche scrape https://docs.python.org --topic "Python async" --depth 2
        cliche scrape https://developer.mozilla.org --topic "JavaScript" --depth 3 --max-pages 10
        cliche scrape https://example.com --depth 1
        cliche scrape https://docs.python.org --images
    """
    # Set environment variable for LLM usage like in the original
    if no_llm:
        os.environ["CLICHE_NO_LLM"] = "1"
        console.print("🔍 LLM extraction disabled, using BeautifulSoup extraction only")
    else:
        # Clear the environment variable if it exists
        if "CLICHE_NO_LLM" in os.environ:
            del os.environ["CLICHE_NO_LLM"]
    
    handle_scrape_command(
        url=url,
        output=output,
        images=images,
        depth=depth,
        max_pages=max_pages,
        topic=topic,
        llm=llm,
        raw=raw,
        save_json=save_json,
        verbose=verbose
    )
