"""
Web scraping command for CLIche.
Enables scraping of a single URL.
"""

import os
import json
import asyncio
import click
import re
import inspect
from pathlib import Path
from rich.console import Console
from ..core import cli, CLIche, get_llm
from ..utils.file import save_text_to_file, get_docs_dir, get_unique_filename
from ..utils.unsplash import UnsplashAPI, format_image_for_markdown, format_image_for_html, get_photo_credit
from cliche.utils.markdown_cleaner import clean_markdown_document

# Initialize console for rich output
console = Console()

# Check if the web crawler package is available
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    
    # Inspect the methods available in AsyncWebCrawler
    # This will help us determine the correct method to use
    CRAWLER_METHODS = [method for method in dir(AsyncWebCrawler) 
                      if not method.startswith('_') and callable(getattr(AsyncWebCrawler, method, None))]
except ImportError:
    AsyncWebCrawler = None
    class CrawlerRunConfig:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    CRAWLER_METHODS = []

# Check if requests package is available (for fallback scraping)
try:
    from bs4 import BeautifulSoup
    FALLBACK_SCRAPER_AVAILABLE = True
except ImportError:
    FALLBACK_SCRAPER_AVAILABLE = False

async def async_scrape(url, topic=None, depth=1, max_pages=3, no_llm=False,
                      include_images=False, max_images=10, min_image_size=100, image_dir=None, debug=False):
    """Scrape structured data from a site based on a topic with multi-page support."""
    # Set environment variable for LLM usage
    if no_llm:
        os.environ["CLICHE_NO_LLM"] = "1"
        click.echo("🔍 LLM extraction disabled, using BeautifulSoup extraction only")
    else:
        if "CLICHE_NO_LLM" in os.environ:
            del os.environ["CLICHE_NO_LLM"]

    console.print(f"🕸️ Scraping {url}")
    console.print(f"⚙️ Settings: depth={depth}, max_pages={max_pages}")
    if debug:
        if depth > 1:
            console.print(f"🔍 Following links {depth} levels deep, max {max_pages} pages total")
            console.print(f"📄 Content limit: {100000 * depth:,} characters total")
            console.print(f"📌 Crawler will stay within {url}'s domain")
        else:
            console.print(f"🔍 Scraping single URL (no link following)")
            console.print(f"📄 Content limit: 100,000 characters")

    if include_images:
        click.echo(f"🖼️ Image extraction enabled: max={max_images}, min_size={min_image_size}px")
        if image_dir:
            click.echo(f"📂 Custom image directory: {image_dir}")
        else:
            click.echo(f"📂 Default image directory: ~/cliche/files/images/scraped")

    # Adjusted crawler configuration for single-site scraping
    crawler_config = CrawlerRunConfig(
        page_timeout=30000,
        wait_until='load',
        scan_full_page=True,
        word_count_threshold=100
    )
    
    # Configure depth-related parameters correctly
    if depth > 1:
        # Set attributes individually rather than during initialization
        # to avoid errors if certain attributes aren't supported by the crawler
        crawler_config.same_domain_only = True
        crawler_config.max_pages = max_pages
        crawler_config.max_links = depth
        
        # Enable follow_links if depth > 1
        # This attribute might not be supported in all versions of crawl4ai
        # so we set it via setattr which will succeed regardless
        setattr(crawler_config, 'follow_links', True)
        
        if debug:
            console.print(f"📊 Crawler Config: following links to depth {depth}, max {max_pages} pages")
    elif debug:
        console.print(f"📊 Crawler Config: single page mode (no link following)")
    
    # Normalize base URL
    if not url.startswith('http'):
        url = 'https://' + url

    try:
        async with AsyncWebCrawler() as crawler:
            try:
                # Extract content using crawler with the config
                extracted_text = await extract_content_with_crawler(crawler, url, crawler_config, debug)
                if extracted_text:
                    click.echo(f"✅ Content extracted: {len(extracted_text)} chars")
                    # Processing extracted text...
                else:
                    click.echo("❌ No content extracted with primary crawler, trying fallback...")
                    extracted_text = await fallback_scrape(url, debug)
            except Exception as e:
                click.echo(f"⚠️ Error during crawling: {str(e)}")
                extracted_text = await fallback_scrape(url, debug)
    except Exception as e:
        click.echo(f"⚠️ Error initializing crawler: {str(e)}")
        extracted_text = await fallback_scrape(url, debug)

    return extracted_text

def extract_text_from_html(html_content):
    """Simple fallback function to extract text from HTML."""
    try:
        if not FALLBACK_SCRAPER_AVAILABLE:
            return "Fallback scraper not available. Please install beautifulsoup4."
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing spaces
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        return f"Error extracting text: {str(e)}"

async def fallback_scrape(url, debug=False):
    """Fallback scraping method using requests and BeautifulSoup."""
    try:
        if not FALLBACK_SCRAPER_AVAILABLE:
            if debug:
                click.echo("  Fallback scraper not available. Need beautifulsoup4.")
            return None
            
        if debug:
            click.echo(f"  Using fallback scraper on {url}")
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        text_content = extract_text_from_html(html_content)
        
        if debug:
            click.echo(f"  Extracted {len(text_content)} chars with fallback scraper")
            
        return text_content
    except Exception as e:
        if debug:
            click.echo(f"  Fallback scraper error: {str(e)}")
        return None

async def extract_content_with_crawler(crawler, url, config, debug=False):
    """Try various methods to extract content with the crawler."""
    if debug:
        click.echo(f"  Available crawler methods: {CRAWLER_METHODS}")
    
    # Check if various methods are available and try them
    content = None
    extracted_text = None
    
    # Try 'arun' method - primary method in current crawl4ai versions
    if 'arun' in CRAWLER_METHODS:
        try:
            if debug:
                click.echo("  Trying crawler.arun() method")
            content = await crawler.arun(url, config)
            if debug:
                click.echo(f"  arun() returned type: {type(content)}")
                if content:
                    if isinstance(content, list):
                        click.echo(f"  Multi-page result with {len(content)} pages")
                    else:
                        click.echo(f"  Content sample: {str(content)[:100]}...")
        except Exception as e:
            if debug:
                click.echo(f"  arun() method failed: {str(e)}")
    
    # Try 'aprocess_html' method - might be useful for pre-fetched HTML
    if content is None and 'aprocess_html' in CRAWLER_METHODS:
        try:
            if debug:
                click.echo("  Trying to fetch page content for aprocess_html")
            # First get the raw HTML
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
            if debug:
                click.echo(f"  Fetched {len(html)} bytes of HTML")
    
            if debug:
                click.echo("  Trying crawler.aprocess_html() method")
            content = await crawler.aprocess_html(html, url, config)
            if debug:
                click.echo(f"  aprocess_html() returned type: {type(content)}")
        except Exception as e:
            if debug:
                click.echo(f"  aprocess_html() method failed: {str(e)}")
    
    # Process content depending on type
    if content is not None:
        max_chars = 100000 * max(1, getattr(config, 'max_links', 1))  # Scale with depth
        
        # Handle list of pages (multi-page crawl results)
        if isinstance(content, list):
            all_text = ""
            count = 0
            
            if debug:
                click.echo(f"  Processing {len(content)} pages, max chars: {max_chars}")
                
            for i, page_content in enumerate(content):
                page_text = extract_text_from_page_content(page_content, debug)
                if page_text:
                    # Add a page separator for better readability
                    if all_text:
                        all_text += "\n\n---\n\n"
                    all_text += page_text
                    count += 1
                    
                    if debug:
                        click.echo(f"  Added page {i+1}: {len(page_text)} chars")
                        
                    # Stop if we've reached the max character limit
                    if len(all_text) >= max_chars:
                        if debug:
                            click.echo(f"  Reached character limit ({max_chars}), stopping")
                        break
            
            if all_text:
                extracted_text = all_text[:max_chars]
                if debug:
                    click.echo(f"  Extracted text from {count} pages: {len(extracted_text)} chars (limit: {max_chars})")
        else:
            # Single page content
            extracted_text = extract_text_from_page_content(content, debug)
            
            # If no text could be extracted, try direct string content
            if extracted_text is None and isinstance(content, str):
                if '<html' in content.lower():
                    extracted_text = extract_text_from_html(content)
                else:
                    extracted_text = content
                
                if extracted_text and len(extracted_text) > max_chars:
                    extracted_text = extracted_text[:max_chars]
                
                if debug and extracted_text:
                    click.echo(f"  Extracted text directly from content string: {len(extracted_text)} chars")
    
    return extracted_text

def extract_text_from_page_content(content, debug=False):
    """Extract text from a page content object."""
    extracted_text = None
    max_length = 0
    
    # Try various attributes that might contain text, prioritizing larger content
    for attr in ['html', 'text', 'content', 'cleaned_html', 'cleaned_text']:
        if hasattr(content, attr):
            text_value = getattr(content, attr)
            if text_value and isinstance(text_value, str) and len(text_value) > 0:
                # Keep track of the longest content found
                if len(text_value) > max_length:
                    max_length = len(text_value)
                    extracted_text = text_value
                    if debug:
                        click.echo(f"  Found text in content.{attr}: {len(text_value)} chars")
    
    # Apply a reasonable limit similar to research.py
    if extracted_text and len(extracted_text) > 100000:
        if debug:
            click.echo(f"  Limiting content from {len(extracted_text)} to 100000 chars")
        extracted_text = extracted_text[:100000]
                
    return extracted_text

@cli.command()
@click.argument("url")
@click.option("--topic", "-t", help="Topic of the scrape")
@click.option("--depth", "-d", type=int, default=3, help="Depth of the scrape")
@click.option("--max-pages", "-m", type=int, default=3, help="Maximum number of pages to crawl")
@click.option("--debug", is_flag=True, help="Enable debug mode with detailed error messages")
@click.option("--fallback-only", is_flag=True, help="Skip primary crawler and use only the fallback scraper")
@click.option("--write", "-w", is_flag=True, help="Generate a document instead of terminal output")
@click.option("--format", "-f", type=click.Choice(['text', 'markdown', 'html']), default='markdown',
              help='Document format when using --write')
@click.option("--filename", help="Optional filename for the generated document")
@click.option("--image", "-i", help='Add images related to the topic by search term', type=str)
@click.option("--image-count", default=3, help='Number of images to add', type=int)
@click.option("--image-width", default=800, help='Width of images', type=int)
@click.option("--search-engine", type=click.Choice(['auto', 'duckduckgo', 'brave']), default='auto',
              help='Search engine to use (auto tries all available)')
@click.option("--summarize", is_flag=True, help="Generate a concise summary document instead of a comprehensive one")
@click.option("--snippet", is_flag=True, help="Generate a very brief snippet/overview (few paragraphs)")

def scrape(url, topic=None, depth=3, max_pages=3, debug=False, fallback_only=False, write=False, format='markdown', 
           filename=None, image=None, image_count=3, image_width=800, search_engine='auto', 
           summarize=False, snippet=False):
    """
    Scrape content from a single website and generate a structured document.
    """

    # Run async_scrape to get the data first
    loop = asyncio.get_event_loop()
    scraped_data = loop.run_until_complete(
        async_scrape(
            url=url,
            topic=topic,
            depth=depth,
            max_pages=max_pages,
            no_llm=fallback_only,
            include_images=bool(image),
            max_images=image_count,
            min_image_size=100,  # Default or configurable
            image_dir=None,  # Default or configurable
            debug=debug
        )
    )
    
    console.print(f"[bold]Scraping... {url}:[/bold]")
    
    # Initialize image data dictionary
    image_data = {"images": [], "credits": []}
    
    # Fetch images if requested for writing mode
    if write and image:
        try:
            unsplash = UnsplashAPI()
            
            # Search for images by term
            console.print(f"🔍 Searching for '{image}' images...")
            results = unsplash.search_photos(image, per_page=image_count)
            
            # Check if we have results
            photos = results.get('results', [])
            if not photos:
                console.print("❌ No images found for this search term.")
            else:
                # Download each image
                for i, photo in enumerate(photos[:image_count]):
                    photo_id = photo.get('id')
                    console.print(f"🖼️ Getting image {i+1}/{min(image_count, len(photos))}...")
                    
                    try:
                        photo_data = unsplash.get_photo_url(photo_id, width=image_width)
                        
                        # Add to image data
                        image_data["images"].append({
                            "url": photo_data["url"],
                            "alt_text": photo_data["alt_text"],
                            "width": image_width
                        })
                        image_data["credits"].append(get_photo_credit(photo, format))
                        
                    except Exception as e:
                        console.print(f"⚠️ Error getting image: {str(e)}")
            
        except Exception as e:
            console.print(f"⚠️ Error fetching images: {str(e)}")
            console.print("Continuing without images...")
    
    # Check if required packages are installed
    if AsyncWebCrawler is None and not FALLBACK_SCRAPER_AVAILABLE:
        click.echo("❌ No web scrapers available. Run: pip install crawl4ai beautifulsoup4")
        return
        
    if debug:
        click.echo("🔍 DEBUG MODE ENABLED")
        if AsyncWebCrawler:
            click.echo(f"Using crawl4ai with AsyncWebCrawler: {AsyncWebCrawler}")
            click.echo(f"Available crawler methods: {CRAWLER_METHODS}")
        if FALLBACK_SCRAPER_AVAILABLE:
            click.echo("Fallback scraper (BeautifulSoup) is available")
        if fallback_only:
            click.echo("Using fallback scraper only (primary crawler disabled)")
        if write:
            click.echo(f"Document generation enabled with format: {format}")
        
    # Use topic as query_str if provided, otherwise use the URL
    query_str = topic if topic else url
    
    # Initialize variable to store extracted data
    extracted_data = []
    
    # Function to actually scrape the site
    async def scrape_and_extract():
        # Only use crawler if available and not in fallback-only mode
        use_crawler = AsyncWebCrawler is not None and not fallback_only
        
        if use_crawler:
            try:
                async with AsyncWebCrawler() as crawler:
                    # Process the single URL directly
                    try:
                        console.print(f"🌐 Scraping: {url}")
                        
                        # Create crawler config
                        config = CrawlerRunConfig(
                            page_timeout=30000,
                            wait_until='load',
                            scan_full_page=True,
                            word_count_threshold=100
                        )
                        
                        # Configure depth-related parameters correctly
                        if depth > 1:
                            # Set attributes individually rather than during initialization
                            # to avoid errors if certain attributes aren't supported by the crawler
                            config.same_domain_only = True
                            config.max_pages = max_pages
                            config.max_links = depth
                            
                            # Enable follow_links if depth > 1
                            setattr(config, 'follow_links', True)
                            
                            if debug:
                                console.print(f"📊 Crawler Config: following links to depth {depth}, max {max_pages} pages")
                        elif debug:
                            console.print(f"📊 Crawler Config: single page mode (no link following)")
                        
                        extracted_text = await extract_content_with_crawler(crawler, url, config, debug)
                        
                        if extracted_text:
                            extracted_data.append({
                                "title": url,
                                "url": url,
                                "content": extracted_text,
                                "snippet": ""
                            })
                            console.print(f"✅ Content extracted: {len(extracted_text)} chars")
                        else:
                            # Try fallback scraping
                            fallback_content = await fallback_scrape(url, debug)
                            
                            max_chars = 100000 * depth  # Scale with depth parameter
                            if fallback_content and len(fallback_content) > 0:
                                extracted_text = fallback_content[:max_chars]  # Scale content size limit with depth
                                extracted_data.append({
                                    "title": url,
                                    "url": url,
                                    "content": extracted_text,
                                    "snippet": ""
                                })
                                console.print(f"✅ Content extracted with fallback: {len(extracted_text)} chars")
                    except Exception as e:
                        error_msg = f"❌ Error scraping {url}: {str(e)}"
                        if debug:
                            import traceback
                            error_msg += f"\n{traceback.format_exc()}"
                        console.print(error_msg)
                        
                        # Always try fallback when crawler fails
                        try:
                            console.print(f"⚠️ Trying fallback scraper after error...")
                            fallback_content = await fallback_scrape(url, debug)
                            
                            max_chars = 100000 * depth  # Scale with depth parameter
                            if fallback_content and len(fallback_content) > 0:
                                extracted_text = fallback_content[:max_chars]  # Scale content size limit with depth
                                extracted_data.append({
                                    "title": url,
                                    "url": url,
                                    "content": extracted_text,
                                    "snippet": ""
                                })
                                console.print(f"✅ Content extracted with fallback: {len(extracted_text)} chars")
                        except Exception as inner_e:
                            if debug:
                                console.print(f"⚠️ Fallback scraper also failed: {str(inner_e)}")
            except Exception as e:
                error_msg = f"❌ Error initializing crawler: {str(e)}"
                if debug:
                    import traceback
                    error_msg += f"\n{traceback.format_exc()}"
                console.print(error_msg)
                console.print("⚠️ Falling back to simple scraper for all URLs")
        
        # If fallback-only mode or crawler failed completely, use fallback on all URLs
        if fallback_only or (not use_crawler) or (use_crawler and not extracted_data):
            # Process the single URL directly
            console.print(f"🌐 {'Scraping' if fallback_only else 'Fallback scraping'}: {url}")
                
            try:
                # Try fallback scraping
                fallback_content = await fallback_scrape(url, debug)
                
                max_chars = 100000 * depth  # Scale with depth parameter
                if fallback_content and len(fallback_content) > 0:
                    extracted_text = fallback_content[:max_chars]  # Scale content size limit with depth
                    extracted_data.append({
                        "title": url,
                        "url": url,
                        "content": extracted_text,
                        "snippet": ""
                    })
            except Exception as e:
                error_msg = f"❌ Error scraping {url}: {str(e)}"
                if debug:
                    import traceback
                    error_msg += f"\n{traceback.format_exc()}"
                console.print(error_msg)
    
    # Run the scraping
    asyncio.run(scrape_and_extract())
    
    if not extracted_data:
        console.print("❌ No content could be extracted from any sources.")
        return 1  # Return error code for better detection in test script
    
    try:
        # Instead of processing all sources at once, we'll chunk them
        all_extracted_data = extracted_data.copy()
        
        # Check if we're generating a snippet or summary (no chunking needed)
        if snippet or summarize:
            # For snippets or summaries, we don't need chunking
            # Combine a limited amount of data from all sources
            combined_sources_info = ""
            source_limit = 2000 if snippet else 5000  # Very limited for snippets
            
            for idx, data in enumerate(all_extracted_data, 1):
                excerpt_length = min(source_limit // len(all_extracted_data), len(data['content']))
                combined_sources_info += f"Source {idx}: {data['title']}\n"
                combined_sources_info += f"URL: {data['url']}\n"
                combined_sources_info += f"Content: {data['content'][:excerpt_length]}...\n\n"
            
            # Create the appropriate template based on format and mode
            if snippet:
                if format == 'markdown':
                    doc_template = """Create a VERY BRIEF SNIPPET (maximum 2-3 paragraphs) about this topic.
                    
                    The snippet should provide a quick overview that could fit in a preview card or executive summary.
                    Include only the most essential information - core definition, key points, and relevance.
                    
                    Keep the total length under 300 words. Use markdown formatting.
                    """
                elif format == 'html':
                    doc_template = """Create a VERY BRIEF SNIPPET (maximum 2-3 paragraphs) about this topic in HTML format. The ENTIRE content must use proper HTML tags, not Markdown.
                    
                    The snippet should provide a quick overview that could fit in a preview card or executive summary.
                    Include only the most essential information - core definition, key points, and relevance.
                    
                    Keep the total length around 500-700 words.

EXTREMELY IMPORTANT: You MUST use HTML tags for EVERYTHING and NEVER use Markdown syntax anywhere in your response.
For example:
- CORRECT: <h1>Main Heading</h1>
- INCORRECT: # Main Heading

- CORRECT: <p>This is a paragraph with <strong>bold text</strong>.</p>
- INCORRECT: This is a paragraph with **bold text**.

- CORRECT: <ul><li>List item</li></ul>
- INCORRECT: - List item

DO NOT EVER USE # FOR HEADINGS OR ** FOR BOLD TEXT OR - FOR LISTS. Always use proper HTML tags.

Every single piece of content must be enclosed in appropriate HTML tags. Do not mix HTML and Markdown syntax anywhere.
                    """
                else:
                    doc_template = """Create a VERY BRIEF SNIPPET (maximum 2-3 paragraphs) about this topic.
                    
                    The snippet should provide a quick overview that could fit in a preview card or executive summary.
                    Include only the most essential information - core definition, key points, and relevance.
                    
                    Keep the total length around 500-700 words.
                    """
            elif summarize:
                if format == 'markdown':
                    doc_template = """
                    Create a CONCISE SUMMARY document about this topic.
                    
                    The summary should be informative but significantly shorter than a comprehensive document.
                    Focus on providing:
                    - Clear definition and overview
                    - Key points and important aspects
                    - Basic background information
                    - Current relevance
                    
                    Keep the length moderate (around 1000-1500 words). Use markdown formatting with appropriate headings.
                    
                    EXTREMELY IMPORTANT:
                    1. DO NOT start your response with ```markdown or any code fences
                    2. DO NOT enclose your entire response in code fences
                    3. Do not use any opening or closing fences in your response
                    """
                elif format == 'html':
                    doc_template = """Create a CONCISE SUMMARY document about this topic in HTML format. The ENTIRE content must use proper HTML tags, not Markdown.
                    
                    The summary should be informative but significantly shorter than a comprehensive document.
                    Focus on providing:
                    - Clear definition and overview
                    - Key points and important aspects
                    - Basic background information
                    - Current relevance
                    
                    Keep the length moderate (around 1000-1500 words).

EXTREMELY IMPORTANT: You MUST use HTML tags for EVERYTHING and NEVER use Markdown syntax anywhere in your response.
For example:
- CORRECT: <h1>Main Heading</h1>
- INCORRECT: # Main Heading

- CORRECT: <p>This is a paragraph with <strong>bold text</strong>.</p>
- INCORRECT: This is a paragraph with **bold text**.

- CORRECT: <ul><li>List item</li></ul>
- INCORRECT: - List item

DO NOT EVER USE # FOR HEADINGS OR ** FOR BOLD TEXT OR - FOR LISTS. Always use proper HTML tags.

Every single piece of content must be enclosed in appropriate HTML tags. Do not mix HTML and Markdown syntax anywhere.
                    """
                else:
                    doc_template = """Create a CONCISE SUMMARY document about this topic.
                    
                    The summary should be informative but significantly shorter than a comprehensive document.
                    Focus on providing:
                    - Clear definition and overview
                    - Key points and important aspects
                    - Basic background information
                    - Current relevance
                    
                    Keep the length moderate (around 1000-1500 words). Use clear paragraph breaks and section indicators.
                    """
            
            # Get image instructions if we have images
            image_instructions = ""
            if image_data["images"] and (format == 'markdown' or format == 'html'):
                # No need for special image placeholder instructions anymore
                image_instructions = "\n\nEXTREMELY IMPORTANT: Do NOT start your response with ```markdown or any code fences. Do NOT enclose your entire response in code fences."
            
            # Build the prompt with image instructions placed prominently
            prompt = f"""
            {doc_template}
            
            {image_instructions}
            
            EXTREMELY IMPORTANT:
            1. DO NOT start your response with ```markdown or any code fences
            2. DO NOT enclose your entire response in code fences
            3. Do not use any opening or closing fences in your response
            
            Topic: {query_str}
            
            Based on the following web scrape results, create a {('snippet' if snippet else 'summary')}:
            
            SCRAPE DATA:
            {combined_sources_info}
            """
            
            console.print(f"🧠 Generating {'snippet' if snippet else 'summary'} for {query_str}...")
            
            # Get the LLM instance
            llm = get_llm()
            
            # Generate content in a single pass
            professional_mode = write  # Use professional mode when generating a document
            response = asyncio.run(llm.generate_response(prompt, professional_mode=professional_mode))
            
            # For markdown, ensure we have a good title
            if format == 'markdown' and not response.strip().startswith("# "):
                title = query_str.title()
                response = f"# {title}\n\n{response}"
        else:
            # Process in chunks of 2 sources at a time
            chunk_size = 2
            chunked_responses = []
            
            for chunk_start in range(0, len(all_extracted_data), chunk_size):
                chunk_end = min(chunk_start + chunk_size, len(all_extracted_data))
                chunk_data = all_extracted_data[chunk_start:chunk_end]
                
                sources_info = ""
                for idx, data in enumerate(chunk_data, chunk_start + 1):
                    sources_info += f"Source {idx}: {data['title']}\n"
                    sources_info += f"URL: {data['url']}\n"
                    sources_info += f"Content: {data['content'][:5000]}...\n\n"
                
                # Create prompt for document generation specific to this chunk
                if format == 'markdown':
                    if chunk_start == 0:  # First chunk includes introduction
                        doc_template = """
                        Create the FIRST PART of an extremely detailed, comprehensive markdown document about this topic.
            
                        Please focus on the INTRODUCTION and FIRST MAJOR SECTIONS of the topic, covering:
                        - Overview and definition of the topic
                        - Historical background and origins
                        - Core concepts and fundamentals
                        - Early developments and pioneers
                        
                        This is the FIRST CHUNK of a multi-part document, so focus on providing a strong foundation.
                        
                        Format with proper markdown headings (## for main sections, ### for subsections).
                        
                        EXTREMELY IMPORTANT:
                        1. DO NOT start your response with ```markdown or any code fences
                        2. DO NOT enclose your entire response in code fences
                        3. Do not use any opening or closing fences in your response
                        """
                    else:  # Continuation chunks
                        doc_template = f"""Create the NEXT PART (part {chunk_start//chunk_size + 1}) of an extremely detailed, comprehensive markdown document about this topic.
            
            Please continue the document with ADDITIONAL SECTIONS covering:
            - Advanced concepts and developments
            - Modern applications and technologies  
            - Current trends and future directions
            - Challenges and limitations
            
            This is a CONTINUATION of a document, so do not include introductory material that would already be covered.
            
            Format with proper markdown headings (## for main sections, ### for subsections).
            
            EXTREMELY IMPORTANT:
            1. DO NOT start your response with ```markdown or any code fences
            2. DO NOT enclose your entire response in code fences
            3. Do not use any opening or closing fences in your response
            """
                elif format == 'html':
                    doc_template = f"""Create part {chunk_start//chunk_size + 1} of a comprehensive HTML document about this topic. The ENTIRE content must use proper HTML tags, not Markdown.

EXTREMELY IMPORTANT: You MUST use HTML tags for EVERYTHING and NEVER use Markdown syntax anywhere in your response.
For example:
- CORRECT: <h1>Main Heading</h1>
- INCORRECT: # Main Heading

- CORRECT: <h2>Section Heading</h2>
- INCORRECT: ## Section Heading

- CORRECT: <p>This is a paragraph with <strong>bold text</strong>.</p>
- INCORRECT: This is a paragraph with **bold text**.

- CORRECT: <ul><li>List item</li><li>Another item</li></ul>
- INCORRECT: - List item
             - Another item

DO NOT EVER USE # FOR HEADINGS OR ** FOR BOLD TEXT OR - FOR LISTS. Always use proper HTML tags like <h1>, <strong>, <ul><li>, etc.

Every single piece of content must be enclosed in appropriate HTML tags. Do not mix HTML and Markdown syntax anywhere."""
                else:
                    doc_template = f"""Create part {chunk_start//chunk_size + 1} of a comprehensive document about this topic in plain text format."""
                
                # Build the chunk-specific prompt
                prompt = f"""
                {doc_template}
                
                Topic: {query_str}
                
                Based on the following web scrape results, create a well-structured document section.
                
                SCRAPE DATA:
                {sources_info}
                
                Make this section detailed, informative, and comprehensive.
                """
                
                console.print(f"🧠 Analyzing chunk {chunk_start//chunk_size + 1} of {(len(all_extracted_data) + chunk_size - 1)//chunk_size}...")
                
                # Get the LLM instance
                llm = get_llm()
                
                try:
                    # Generate content for this chunk
                    professional_mode = write  # Use professional mode when generating a document
                    chunk_response = asyncio.run(llm.generate_response(prompt, professional_mode=professional_mode))
                    chunked_responses.append(chunk_response)
                except Exception as e:
                    console.print(f"❌ Error generating response for chunk {chunk_start//chunk_size + 1}: {str(e)}")
                    continue
            
            # Combine all chunk responses into a single document
            if chunked_responses:
                response = "\n\n".join(chunked_responses)
                
                # For markdown, ensure we have a good title and table of contents
                if format == 'markdown' and not response.strip().startswith("# "):
                    title = query_str.title()
                    response = f"# {title}\n\n{response}"
                
                # Clean up any stray markdown code fences - import if needed
                if format == 'markdown':
                    response = clean_markdown_document(response)
                
                # Clean up any stray markdown code fences from HTML content
                if format == 'html':
                    # Remove any markdown code fences that might appear in the HTML content
                    response = re.sub(r'```html\s*', '', response)
                    response = re.sub(r'```\s*', '', response)
                    
                    # Convert headings (all levels h1-h6)
                    response = re.sub(r'^#{1}\s+(.+?)$', r'<h1>\1</h1>', response, flags=re.MULTILINE)
                    response = re.sub(r'^#{2}\s+(.+?)$', r'<h2>\1</h2>', response, flags=re.MULTILINE)
                    response = re.sub(r'^#{3}\s+(.+?)$', r'<h3>\1</h3>', response, flags=re.MULTILINE)
                    response = re.sub(r'^#{4}\s+(.+?)$', r'<h4>\1</h4>', response, flags=re.MULTILINE)
                    response = re.sub(r'^#{5}\s+(.+?)$', r'<h5>\1</h5>', response, flags=re.MULTILINE)
                    response = re.sub(r'^#{6}\s+(.+?)$', r'<h6>\1</h6>', response, flags=re.MULTILINE)
                    
                    # Convert bold text
                    response = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', response)
                    
                    # Convert italic text
                    response = re.sub(r'\*(.+?)\*', r'<em>\1</em>', response)
                    
                    # Convert list items
                    response = re.sub(r'^\s*-\s+(.+?)$', r'<li>\1</li>', response, flags=re.MULTILINE)
                    
                    # Wrap adjacent list items in <ul> tags
                    list_pattern = r'(<li>.*?</li>\s*){2,}'
                    matches = re.finditer(list_pattern, response, re.DOTALL)
                    for match in matches:
                        orig = match.group(0)
                        wrapped = f'<ul>{orig}</ul>'
                        response = response.replace(orig, wrapped)
                    
                    # Ensure all paragraphs are wrapped in <p> tags
                    # Find text that's not inside any HTML tags and wrap it with <p>
                    lines = response.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip() and not re.match(r'^\s*<', line) and not re.match(r'^\s*$', line):
                            # If it's not already in an HTML tag, wrap it
                            lines[i] = f'<p>{line}</p>'
                    response = '\n'.join(lines)
                
                # Clean up any legacy [INSERT_IMAGE_X_HERE] placeholders that might appear
                response = re.sub(r'\[INSERT_IMAGE_\d+_HERE\]', '', response)
            else:
                console.print("❌ No content could be generated from any chunks.")
                return 1  # Return error code
        
        # Process the generated content to replace image placeholders
        if image_data["images"] and (format == 'markdown' or format == 'html'):
            console.print(f"🖼️ Processing {len(image_data['images'])} images for document")
            
            # Check if any IMAGE_ placeholders are in the document
            placeholders_found = len(re.findall(r'\bIMAGE_\d+\b', response))
            
            # Also check for [INSERT_IMAGE_X_HERE] pattern
            insert_placeholders_found = len(re.findall(r'\[INSERT_IMAGE_\d+_HERE\]', response))
            placeholders_found += insert_placeholders_found
            
            # If no placeholders found, use AI-powered image placement
            if placeholders_found == 0:
                console.print("💡 Using AI-powered image placement to enhance the document...")
                
                # Split response into paragraphs for placement
                paragraphs = response.split('\n\n')
                
                # Get LLM recommendations for image placement
                insertion_points = None
                try:
                    insertion_points = asyncio.run(get_image_placement_suggestions(
                        llm=llm, 
                        document_content=response, 
                        image_count=len(image_data["images"]),
                        topic=query_str,
                        format=format
                    ))
                except Exception as e:
                    console.print(f"⚠️ Error getting image placement suggestions: {str(e)}")
                    insertion_points = None
                
                # If LLM suggestions aren't available or valid, fallback to our distribution method
                if not insertion_points:
                    # Find headings to identify section breaks
                    heading_indices = [i for i, p in enumerate(paragraphs) if p.startswith('#')]
                    
                    # If we have enough headings, distribute images after headings
                    if len(heading_indices) >= len(image_data["images"]):
                        # Choose evenly spaced heading indices
                        step = len(heading_indices) // (len(image_data["images"]) + 1)
                        if step < 1:
                            step = 1
                        
                        insertion_points = []
                        for i in range(1, len(image_data["images"]) + 1):
                            idx = min(i * step, len(heading_indices) - 1)
                            heading_idx = heading_indices[idx]
                            insertion_point = min(heading_idx + 1, len(paragraphs) - 1)
                            if insertion_point not in insertion_points:
                                insertion_points.append(insertion_point)
                    else:
                        # Not enough headings, distribute evenly throughout document
                        total_paragraphs = len(paragraphs)
                        spacing = total_paragraphs // (len(image_data["images"]) + 1)
                        
                        # Ensure we don't insert at the beginning
                        start_point = min(4, total_paragraphs // 10)
                        
                        insertion_points = []
                        for i in range(len(image_data["images"])):
                            # Calculate position ensuring even distribution
                            pos = start_point + (i + 1) * spacing
                            pos = min(pos, total_paragraphs - 1)
                            
                            # Avoid inserting before headings
                            if pos < total_paragraphs - 1 and paragraphs[pos + 1].startswith('#'):
                                pos += 2
                            
                            if pos not in insertion_points and pos < total_paragraphs:
                                insertion_points.append(pos)
                
                # Sort insertion points
                if insertion_points:
                    insertion_points.sort()
                    
                    # Make sure we don't have more insertion points than images
                    insertion_points = insertion_points[:len(image_data["images"])]
                    
                    # Insert images at the chosen points
                    for i, insertion_idx in enumerate(insertion_points):
                        if i < len(image_data["images"]):
                            img_data = image_data["images"][i]
                            img_alt = img_data["alt_text"] or "Image"
                            
                            if format == 'markdown':
                                img_content = f"\n\n![{img_alt}]({img_data['url']})\n\n"
                            else:  # HTML format
                                img_content = f"\n\n<img src=\"{img_data['url']}\" alt=\"{img_alt}\" style=\"max-width: 100%; height: auto;\">\n\n"
                                
                            paragraphs.insert(insertion_idx + i, img_content)
                    
                    # Reconstruct the document
                    response = '\n\n'.join(paragraphs)
            else:
                # Handle explicit placeholders
                console.print(f"🔄 Processing {placeholders_found} image placeholders...")
                
                # Replace placeholders with actual images
                for i, img_data in enumerate(image_data["images"]):
                    img_idx = i + 1
                    if img_idx <= placeholders_found:
                        placeholder = f"IMAGE_{img_idx}"
                        if format == 'markdown':
                            img_content = f"![{img_data['alt_text'] or 'Image'}]({img_data['url']})"
                        else:  # HTML
                            img_content = f"<img src=\"{img_data['url']}\" alt=\"{img_data['alt_text'] or 'Image'}\" style=\"max-width: 100%; height: auto;\">"
                        
                        response = response.replace(placeholder, img_content)
            
            # Add credits at the end of the document
            if image_data["credits"]:
                if format == 'markdown':
                    response += "\n\n---\n\n## Image Credits\n\n"
                    for credit in image_data["credits"]:
                        response += f"* {credit}\n"
                else:  # HTML
                    response += "\n\n<hr>\n<h2>Image Credits</h2>\n<ul>\n"
                    for credit in image_data["credits"]:
                        response += f"<li>{credit}</li>\n"
                    response += "</ul>\n"
        
        # Determine what to do with the response based on write flag
        if write:
            # Get format-specific extension
            if format == 'markdown':
                ext = '.md'
            elif format == 'html':
                ext = '.html'
            else:
                ext = '.txt'
            
            # Generate default filename if none provided
            if not filename:
                # Create a filename from the first few words of the query
                words = query_str.lower().split()[:3]
                base_filename = 'scrape_' + '_'.join(words) + ext
                # Use the docs/scrape directory for organization
                output_dir = get_docs_dir('scrape')
                # Get a unique filename
                unique_filename = get_unique_filename(output_dir, base_filename)
                file_path = str(output_dir / unique_filename)
            else:
                # Make sure filename has correct extension
                if not any(filename.endswith(e) for e in ['.txt', '.md', '.html']):
                    filename += ext
                
                # Use specified filename, but ensure it's in the right directory
                if os.path.dirname(filename):
                    # If a full path is provided, use it
                    file_path = filename
                else:
                    # Otherwise, put it in the docs/scrape directory
                    output_dir = get_docs_dir('scrape')
                    # Get a unique filename
                    unique_filename = get_unique_filename(output_dir, filename)
                    file_path = str(output_dir / unique_filename)
            
            # Ensure HTML has proper structure
            if format == 'html' and not response.strip().startswith('<!DOCTYPE html>'):
                response = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{query_str} - Scrape</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        img {{ max-width: 100%; height: auto; display: block; margin: 20px 0; }}
        code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        h1, h2, h3 {{ color: #333; }}
        .unsplash-image {{ border-radius: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
{response}
</body>
</html>"""
            
            # Save to file
            save_text_to_file(response, file_path)
            console.print(f"✅ Scrape document saved to: {file_path}")
        else:
            # Display the response in terminal
            console.print("\n" + "=" * 60)
            console.print("📚 SCRAPE RESULTS")
            console.print("=" * 60)
            console.print(f"\n💡 {response}\n")
            console.print("=" * 60)
            console.print(f"Sources: {len(extracted_data)} website analyzed")
            console.print("=" * 60)
        
        return 0  # Return success code
        
    except AttributeError as e:
        console.print("❌ Error: Provider not properly configured")
        return 1  # Return error code
    except Exception as e:
        console.print(f"❌ Error generating response: {str(e)}")
        return 1  # Return error code


async def get_image_placement_suggestions(llm, document_content, image_count, topic, format):
    """Ask the LLM to suggest optimal image placement locations in the document.
    
    Args:
        llm: The LLM instance to use
        document_content: The content of the document to analyze
        image_count: Number of images to place
        topic: The document topic
        format: The document format (markdown, html)
        
    Returns:
        A list of suggested paragraph indices where images should be placed
    """
    # Create a prompt specifically for image placement
    placement_prompt = f"""
    I've generated a {format} document about "{topic}". Now I need to place {image_count} images at optimal locations.
    
    Please analyze this document and suggest the {image_count} best locations to place relevant images.
    
    For each suggested location:
    1. Identify the paragraph number (counting from 0)
    2. Explain why this is a good location (e.g., introduces a key concept, visualizes an example)
    
    Your response should be in this format:
    PLACEMENT 1: Paragraph X - Reason
    PLACEMENT 2: Paragraph Y - Reason
    ... and so on
    
    Here's the document content:
    ---
    {document_content}
    ---
    
    IMPORTANT: Focus on finding contextually relevant placements where images would enhance understanding.
    """
    
    # Get suggestions from the LLM
    response = await llm.generate_response(placement_prompt, professional_mode=True)
    
    # Parse the response to extract paragraph indices
    suggested_indices = []
    
    # Look for "PLACEMENT X: Paragraph Y" patterns
    placement_pattern = r'PLACEMENT\s+\d+\s*:\s*Paragraph\s+(\d+)'
    matches = re.finditer(placement_pattern, response)
    
    for match in matches:
        try:
            paragraph_index = int(match.group(1))
            suggested_indices.append(paragraph_index)
        except:
            continue
    
    # If we couldn't extract valid suggestions, fallback to evenly distributed placements
    if not suggested_indices or len(suggested_indices) < image_count:
        # Our existing fallback method which evenly distributes images
        return None
    
    # Return only up to the requested number of placements
    return suggested_indices[:image_count]

if __name__ == "__main__":
    research()
