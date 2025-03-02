"""CLI interface for the scraping functionality."""
import os
import json
import asyncio
import click
import logging
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from typing import Optional, Dict, Any, List

from .extractors.manager import get_extractor_manager
from .models.data_models import ExtractionResult
from ..utils.file import get_image_dir

class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def async_scrape(url: str, topic: Optional[str] = None, depth: int = 1, max_pages: int = 3, 
                      no_llm: bool = False, include_images: bool = False, max_images: int = 10, 
                      min_image_size: int = 100, image_dir: Optional[str] = None) -> bool:
    """Scrape structured data from a site based on a topic with multi-page support."""
    # Configure logging
    logging.basicConfig(level=logging.DEBUG if "CLICHE_DEBUG" in os.environ else logging.INFO)
    logger = logging.getLogger(__name__)

    # Set environment variable for LLM usage
    if no_llm:
        os.environ["CLICHE_NO_LLM"] = "1"
        click.echo("🔍 LLM extraction disabled, using standard extraction only")
    elif "CLICHE_NO_LLM" in os.environ:
        del os.environ["CLICHE_NO_LLM"]

    # Normalize URL
    if not url.startswith('http'):
        url = 'https://' + url

    click.echo(f"🕸️ Scraping {url}" + (f" for topic: '{topic}'" if topic else ""))
    click.echo(f"⚙️ Settings: depth={depth}, max_pages={max_pages}" + (", no-llm=True" if no_llm else ""))

    if include_images:
        click.echo(f"🖼️ Image extraction enabled: max={max_images}, min_size={min_image_size}px")
        if image_dir:
            click.echo(f"📂 Custom image directory: {image_dir}")
        else:
            click.echo(f"📂 Default image directory: ~/cliche/files/images/scraped")

    # Get the extractor manager
    manager = get_extractor_manager()
    visited = set()
    results = []

    try:
        # Queue of URLs to process (url, depth)
        to_visit = [(url, 1)]
        
        while to_visit and len(visited) < max_pages:
            current_url, current_depth = to_visit.pop(0)
            
            if current_url in visited:
                continue
                
            visited.add(current_url)
            logger.debug(f"Processing URL: {current_url} at depth {current_depth}")
            
            # Extract content using appropriate extractor
            extraction_result = await manager.extract(
                url=current_url,
                topic=topic,
                include_images=include_images,
                max_images=max_images,
                min_image_size=min_image_size,
                image_dir=image_dir
            )

            if extraction_result.success and extraction_result.data:
                results.append(extraction_result.data)
                click.echo(f"✅ Successfully extracted content from {current_url}")
                
                # Handle discovered links if depth allows
                if current_depth < depth and extraction_result.links:
                    for link in extraction_result.links:
                        if (link not in visited and is_same_domain(url, link) and 
                            len(visited) < max_pages):
                            to_visit.append((link, current_depth + 1))

            else:
                logger.warning(f"Failed to extract content from {current_url}: {extraction_result.error}")

        if not results:
            click.echo(f"❌ No content could be extracted from {url}")
            return False

        # Save results
        success = await save_results(results, url, topic)
        
        # Clean up resources
        manager.cleanup()
        
        return success

    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}", exc_info=True)
        click.echo(f"❌ Error during scraping: {str(e)}")
        return False

async def save_results(results: list, url: str, topic: Optional[str] = None) -> bool:
    """Save scraped results to JSON files."""
    saved_files = []
    success = False

    try:
        for idx, data in enumerate(results):
            # Create unique filename
            domain = urlparse(url).netloc.replace('.', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if topic:
                base_filename = f"scraped_{domain}_{topic}"
            else:
                base_filename = f"scraped_{domain}"
                
            if len(results) > 1:
                base_filename = f"{base_filename}_{idx+1}"
                
            base_filename = f"{base_filename}_{timestamp}"
            
            # Create output directory
            output_dir = Path(os.path.expanduser("~/cliche/files/scrape"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save JSON file with custom encoder for datetime
            output_path = output_dir / f"{base_filename}.json"
            
            with open(output_path, "w") as f:
                if hasattr(data, 'model_dump'):  # Pydantic v2
                    json.dump(data.model_dump(), f, indent=2, cls=DateTimeEncoder)
                elif hasattr(data, 'dict'):  # Pydantic v1
                    json.dump(data.dict(), f, indent=2, cls=DateTimeEncoder)
                else:
                    json.dump(data, f, indent=2, cls=DateTimeEncoder)
            
            click.echo(f"✅ Saved content to {output_path}")
            saved_files.append(str(output_path))
            
            # Show image extraction stats if available
            images = getattr(data, 'images', None) or data.get('images', [])
            if images:
                click.echo(f"🖼️ Extracted {len(images)} images")
                # Show image directory if available
                first_image = images[0]
                if isinstance(first_image, dict):
                    image_path = first_image.get('local_path')
                else:
                    image_path = getattr(first_image, 'local_path', None)
                    
                if image_path:
                    image_dir = os.path.dirname(str(image_path))
                    click.echo(f"📂 Images saved to {image_dir}")
            
            success = True

        # Final summary
        if saved_files:
            click.echo("\n📄 Summary of saved files:")
            for file_path in saved_files:
                click.echo(f"  - {file_path}")

    except Exception as e:
        logging.error(f"Error saving results: {str(e)}", exc_info=True)
        click.echo(f"❌ Error saving results: {str(e)}")
        success = False

    return success

def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs belong to the same domain."""
    return urlparse(url1).netloc == urlparse(url2).netloc 