import os
import json
import asyncio
import threading
import click
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field
from ..core import CLIche, get_llm
from bs4 import BeautifulSoup
from pathlib import Path
import requests
from ..utils.file import get_unique_filename, get_scraped_images_dir, get_image_dir
import re
from ..utils.image_scraper import extract_and_download_images, extract_and_download_images_async, ScrapedImage
from typing import Optional, List, Dict, Any
import hashlib
from datetime import datetime
from ..models.scrape_models import ScrapedData
from ..utils.url_utils import is_same_domain, is_url_relevant, is_wikipedia_url, is_python_org_url
from ..utils.content_utils import is_relevant_content, process_code_block, extract_table_as_markdown, process_div_content
from ..extractors.wikipedia_extractor import extract_wikipedia
from ..extractors.python_org_extractor import extract_python_org
from ..extractors.generic_extractor import extract_generic

# --- Scraping Logic ---
async def scrape_page(crawler, url, base_url, visited, topic=None, include_images=False, max_images=10, min_image_size=100, image_dir=None):
    """Scrape a page and return structured data if relevant."""
    try:
        # Check if it's a special page that needs custom handling
        if is_wikipedia_url(url):
            click.echo("📚 Using specialized Wikipedia extraction")
            result = await extract_wikipedia(url, topic, include_images, max_images, min_image_size, image_dir)
            return result
        
        # Check for Python.org pages which need specialized extraction
        if is_python_org_url(url):
            click.echo("DEBUG: Using specialized Python.org extraction")
            result = await extract_python_org(url, topic, include_images, max_images, min_image_size, image_dir)
            return result
            
        # Use the generic extractor for all other sites
        result = await extract_generic(url, crawler, base_url, visited, topic, include_images, max_images, min_image_size, image_dir)
        return result
    
    except Exception as e:
        click.echo(f"⚠️ Error during scraping: {str(e)}")
        import traceback
        click.echo(f"Debug details: {traceback.format_exc()}")
        return None, []

async def crawl_site(url, topic=None, max_depth=2, max_pages=5, include_images=False, max_images=10, min_image_size=100, image_dir=None):
    """Crawl a site to a certain depth, focusing on relevant content."""
    
    # For debugging
    print(f"DEBUG: Starting site crawl of {url} with depth {max_depth}")
    
    # Visited pages set and results dict
    visited = set()
    results = {}
    
    # Create crawler instance
    crawler = AsyncWebCrawler()
    
    # Queue of pages to visit (url, depth)
    to_visit = [(url, 1)]

    # Dictionary to store all scraped data
    all_data = {}
    
    while to_visit and len(visited) < max_pages:
        current_url, depth = to_visit.pop(0)
        
        if current_url in visited:
            continue
            
        visited.add(current_url)
        
        click.echo(f"🕸️ Crawling ({depth}/{max_depth}): {current_url}")
        
        try:
            print(f"DEBUG: Scraping page {current_url}")
            data, links = await scrape_page(
                crawler, current_url, url, visited, topic, 
                include_images, max_images, min_image_size, image_dir
            )
            
            # Save information to our accumulator
            if data:
                all_data[current_url] = data
                
                # Debug info about images
                if 'images' in data and data['images']:
                    print(f"DEBUG: Page has {len(data['images'])} images")
                else:
                    print(f"DEBUG: Page has no images")
            
            if depth < max_depth:
                link_count = 0
                for link in links:
                    if link not in visited and is_same_domain(url, link):
                        # Check link relevance based on URL text
                        if is_url_relevant(link, topic):
                            to_visit.append((link, depth + 1))
                            link_count += 1
                print(f"DEBUG: Found {link_count} relevant links to follow")
        except Exception as e:
            import traceback
            print(f"DEBUG: Error scraping {current_url}: {str(e)}")
            print(f"DEBUG: Error details: {traceback.format_exc()}")
    
    print(f"DEBUG: Crawl complete. Found {len(results)} relevant pages")
    return results

# --- Scraping APIs ---
async def scrape_url(url, depth=2, max_pages=50, llm_processing=True, topic=None, include_images=False, max_images=10, min_image_size=100, image_directory=None):
    """Scrape a URL and all relevant linked pages up to max_depth."""
    # Create output directories if they don't exist
    os.makedirs(get_scraped_images_dir(), exist_ok=True)
    
    # Generate a unique output directory for images in this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if image_directory:
        image_dir = Path(image_directory)
    else:
        domain = urlparse(url).netloc.replace('.', '_').replace(':', '_')
        # Get the base image directory and then create a subdirectory
        base_image_dir = get_image_dir()
        image_dir = base_image_dir / f"{domain}_{timestamp}"
        
    if include_images:
        os.makedirs(image_dir, exist_ok=True)
        click.echo(f"🖼️ Saving images to {image_dir}")
    
    # Update environment for LLM control
    if not llm_processing:
        os.environ["CLICHE_NO_LLM"] = "1"
        click.echo("🤖 LLM extraction disabled, using BeautifulSoup extraction only")
    else:
        if "CLICHE_NO_LLM" in os.environ:
            del os.environ["CLICHE_NO_LLM"]
            
    # Set up the crawler
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    visited = set()
    all_results = []
    
    # Create the crawler with a custom extraction strategy if requested
    print(f"DEBUG: Creating AsyncWebCrawler (LLM enabled: {llm_processing})")
    crawler = AsyncWebCrawler()
    
    # Process the starting URL
    click.echo(f"🕸️ Starting crawl from {url} with depth {depth}, max pages: {max_pages}")
    to_visit = [(url, 0)]  # (url, depth)
    
    while to_visit and len(visited) < max_pages:
        current_url, current_depth = to_visit.pop(0)
        
        if current_url in visited:
            continue
            
        visited.add(current_url)
        click.echo(f"🔍 Processing {current_url} (depth {current_depth}/{depth})")
        
        # Scrape the current page
        result_data, links = await scrape_page(
            crawler=crawler,
            url=current_url,
            base_url=base_url,
            visited=visited,
            topic=topic,
            include_images=include_images,
            max_images=max_images,
            min_image_size=min_image_size,
            image_dir=image_dir
        )
        
        if result_data:
            click.echo(f"✅ Successfully extracted content from {current_url}")
            
            # Create slug from URL for unique identification
            url_slug = hashlib.md5(current_url.encode()).hexdigest()[:10]
            
            # Skip images when printing the preview
            result_copy = result_data.copy()
            if "images" in result_copy:
                image_count = len(result_copy["images"])
                del result_copy["images"]
                click.echo(f"📸 Found {image_count} images (not shown in preview)")
                
            # Print a preview of what was extracted
            extracted_preview = str(result_copy)
            if len(extracted_preview) > 500:
                extracted_preview = extracted_preview[:500] + "..."
            click.echo(f"📄 Extracted: {extracted_preview}")
            
            # Add the current URL to the result
            result_data["url"] = current_url
            result_data["page_depth"] = current_depth
            result_data["crawl_timestamp"] = datetime.now().isoformat()
            
            all_results.append(result_data)
            
            # If we haven't reached max depth, add links to the queue
            if current_depth < depth:
                for link in links:
                    # Skip links that are not on the same domain
                    if not is_same_domain(link, base_url):
                        continue
                        
                    # Skip links that are not relevant
                    if not is_url_relevant(link):
                        continue
                        
                    # Skip links we've already visited or queued
                    if link in visited or any(link == url for url, _ in to_visit):
                        continue
                        
                    to_visit.append((link, current_depth + 1))
                    
    if all_results:
        # Save the extracted data
        output_path = f"{os.getcwd()}/files/scrape"
        os.makedirs(output_path, exist_ok=True)
        
        domain = urlparse(url).netloc.replace(".", "_")
        filename = f"scraped_{domain}_{timestamp}.json"
        output_file = os.path.join(output_path, filename)
        
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2)
            
        click.echo(f"💾 Saved {len(all_results)} pages to {output_file}")
        
        # Return the path where data was saved
        return {"file": output_file, "pages": len(all_results)}
    else:
        click.echo("⚠️ No content was extracted")
        return None

# --- CLI Command ---
@click.command()
@click.argument("url", required=True)
@click.option("--output", "-o", help="Output file path")
@click.option("--depth", "-d", default=1, help="Crawl depth (default: 1)")
@click.option("--max-pages", "-p", default=3, help="Maximum pages to crawl (default: 3)")
@click.option("--no-llm", is_flag=True, help="Disable LLM extraction, use BeautifulSoup only")
@click.option("--topic", "-t", help="Topic to filter content by relevance")
@click.option("--include-images", is_flag=True, help="Extract and download images")
@click.option("--max-images", default=10, help="Maximum images to extract per page (default: 10)")
@click.option("--min-image-size", default=100, help="Minimum image size in pixels (default: 100x100)")
@click.option("--image-dir", help="Directory to save images (default: auto-generated)")
@click.pass_obj
def scrape(cliche, url, output, depth, max_pages, no_llm, topic, include_images, max_images, min_image_size, image_dir):
    """Scrape a URL and extract relevant content with optional LLM processing."""
    click.echo(f"🕸️ Scraping content from {url}")
    click.echo(f"🔍 Depth: {depth}, Max pages: {max_pages}, No-LLM: {no_llm}")
    
    # Check if URL is valid
    if not url.startswith(("http://", "https://")):
        click.echo("⚠️ URL must start with http:// or https://")
        return
        
    # Run the scraper in an async context
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        scrape_url(
            url=url, 
            depth=depth, 
            max_pages=max_pages, 
            llm_processing=not no_llm,
            topic=topic,
            include_images=include_images,
            max_images=max_images,
            min_image_size=min_image_size,
            image_directory=image_dir
        )
    )
    
    if result:
        click.echo("✅ Scraping complete")
        click.echo(f"💾 Saved {result['pages']} pages to {result['file']}")
        
        # Extract the filename without the path
        filename = os.path.basename(result['file'])
        base_name = os.path.splitext(filename)[0]
        
        # Get the portion after "scraped_"
        if base_name.startswith("scraped_"):
            base_name = base_name[len("scraped_"):]
            
        click.echo(f"💡 Tip: Run 'cliche generate {base_name}' to create a document from the scraped data")
    else:
        click.echo("⚠️ Scraping failed or no relevant content found")
