"""
Web research command for CLIche.
Enables research with up-to-date web content.
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

# Initialize console for rich output
console = Console()

# Check if the DuckDuckGo search package is available
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

# Check if the web crawler package is available
try:
    from crawl4ai import AsyncWebCrawler
    
    # Inspect the methods available in AsyncWebCrawler
    # This will help us determine the correct method to use
    CRAWLER_METHODS = [method for method in dir(AsyncWebCrawler) 
                      if not method.startswith('_') and callable(getattr(AsyncWebCrawler, method, None))]
    
    try:
        # Try to import CrawlerRunConfig - it might have different name in different versions
        from crawl4ai import CrawlerRunConfig
    except ImportError:
        # Fallback to a simple config class if not available
        class CrawlerRunConfig:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
except ImportError:
    AsyncWebCrawler = None
    CRAWLER_METHODS = []

# Check if requests package is available (for fallback scraping)
try:
    import requests
    from bs4 import BeautifulSoup
    FALLBACK_SCRAPER_AVAILABLE = True
except ImportError:
    FALLBACK_SCRAPER_AVAILABLE = False

def perform_search(query, num_results=5):
    """Perform a DuckDuckGo search and return the top results."""
    if DDGS is None:
        click.echo("❌ DuckDuckGo search package not installed. Run: pip install duckduckgo-search")
        return []
        
    with DDGS() as ddgs:
        try:
            results = []
            for r in ddgs.text(query, max_results=num_results):
                # Ensure we have a valid URL and title
                url = r.get('href', '')
                title = r.get('title', '')
                
                if not url or not title:
                    continue
                    
                results.append({
                    'link': url,
                    'title': title,
                    'snippet': r.get('body', '')
                })
            return results
        except Exception as e:
            click.echo(f"Error during search: {str(e)}")
            return []

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
    
    # Try 'crawl' method
    if 'crawl' in CRAWLER_METHODS:
        try:
            if debug:
                click.echo("  Trying crawler.crawl() method")
            content = await crawler.crawl(url, config)
            if debug:
                click.echo(f"  crawl() returned type: {type(content)}")
        except Exception as e:
            if debug:
                click.echo(f"  crawl() method failed: {str(e)}")
    
    # Try 'extract_content' method
    if content is None and 'extract_content' in CRAWLER_METHODS:
        try:
            if debug:
                click.echo("  Trying crawler.extract_content() method")
            content = await crawler.extract_content(url, config)
            if debug:
                click.echo(f"  extract_content() returned type: {type(content)}")
        except Exception as e:
            if debug:
                click.echo(f"  extract_content() method failed: {str(e)}")
    
    # Try 'fetch' method
    if content is None and 'fetch' in CRAWLER_METHODS:
        try:
            if debug:
                click.echo("  Trying crawler.fetch() method")
            content = await crawler.fetch(url, config)
            if debug:
                click.echo(f"  fetch() returned type: {type(content)}")
        except Exception as e:
            if debug:
                click.echo(f"  fetch() method failed: {str(e)}")
    
    # Try to extract text from content object
    if content is not None:
        # Try various attributes that might contain text
        for attr in ['text', 'cleaned_text', 'content', 'cleaned_html', 'html']:
            if hasattr(content, attr):
                text_value = getattr(content, attr)
                if text_value and isinstance(text_value, str) and len(text_value) > 100:
                    extracted_text = text_value[:3000]  # Limit content size
                    if debug:
                        click.echo(f"  Found text in content.{attr}: {len(extracted_text)} chars")
                    break
    
    # If no text found, try the simplest approach - get content as string
    if extracted_text is None and content is not None:
        try:
            text_str = str(content)
            if len(text_str) > 100 and '<html' in text_str.lower():
                extracted_text = extract_text_from_html(text_str)[:3000]
                if debug:
                    click.echo(f"  Extracted {len(extracted_text)} chars from str(content)")
        except Exception as e:
            if debug:
                click.echo(f"  Error extracting text from content: {str(e)}")
    
    return extracted_text

@cli.command()
@click.argument("query", nargs=-1)
@click.option("--depth", "-d", type=int, default=3, help="Number of search results to analyze")
@click.option("--debug", is_flag=True, help="Enable debug mode with detailed error messages")
@click.option("--fallback-only", is_flag=True, help="Skip primary crawler and use only the fallback scraper")
@click.option("--write", "-w", is_flag=True, help="Generate a document instead of terminal output")
@click.option("--format", "-f", type=click.Choice(['text', 'markdown', 'html']), default='markdown',
              help='Document format when using --write')
@click.option("--filename", help="Optional filename for the generated document")
@click.option("--image", "-i", help='Add images related to the topic by search term', type=str)
@click.option("--image-count", default=3, help='Number of images to add', type=int)
@click.option("--image-width", default=800, help='Width of images', type=int)
def research(query, depth, debug, fallback_only, write, format, filename, 
             image, image_count, image_width):
    """Research a topic online and generate a response or document.
    
    Research uses web search and content extraction to provide up-to-date information
    on any topic. The results are processed by an AI to create a comprehensive
    response or document.
    
    Examples:
      cliche research "Latest developments in quantum computing"
      cliche research "Python async programming best practices" -d 5
      cliche research "Climate change impacts" --write --format markdown
      cliche research "Mars exploration" -w -f markdown --image "mars rover" --image-count 2
    """
    
    # Join query parts
    query_str = ' '.join(query)
    
    if not query_str:
        console.print("[bold red]Please provide a search query.[/bold red]")
        console.print("Example: cliche research \"Latest developments in quantum computing\"")
        return
    
    console.print(f"[bold]Researching:[/bold] {query_str}")
    
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
    if DDGS is None:
        click.echo("❌ DuckDuckGo search package not installed. Run: pip install duckduckgo-search")
        return
        
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
        
    console.print(f"🔍 Researching: {query_str}...")

    # Perform a web search
    search_results = perform_search(query_str, num_results=depth)

    if not search_results:
        click.echo("❌ No search results found.")
        return
    
    # Select top N results
    selected_results = search_results[:depth]
    
    extracted_data = []
    
    async def scrape_and_extract():
        # Only use crawler if available and not in fallback-only mode
        use_crawler = AsyncWebCrawler is not None and not fallback_only
        
        if use_crawler:
            try:
                async with AsyncWebCrawler() as crawler:
                    for result in selected_results:
                        url = result['link']
                        title = result['title']
                        
                        if not url:
                            continue
                        
                        console.print(f"🌐 Scraping: {title}")
                        
                        try:
                            if debug:
                                console.print(f"  Creating crawler config for {url}")
                            
                            config = CrawlerRunConfig(
                                page_timeout=30000,
                                wait_until='load',
                                scan_full_page=True,
                                word_count_threshold=100
                            )
                            
                            extracted_text = await extract_content_with_crawler(crawler, url, config, debug)
                            
                            if extracted_text:
                                extracted_data.append({
                                    "title": title,
                                    "url": url,
                                    "content": extracted_text,
                                    "snippet": result.get('snippet', '')
                                })
                                console.print(f"✅ Content extracted: {len(extracted_text)} chars")
                            else:
                                # Try fallback scraping
                                # Try alternate extraction method
                                fallback_content = await fallback_scrape(url, debug)
                                
                                if fallback_content and len(fallback_content) > 100:
                                    extracted_text = fallback_content[:3000]  # Limit content size
                                    extracted_data.append({
                                        "title": title,
                                        "url": url,
                                        "content": extracted_text,
                                        "snippet": result.get('snippet', '')
                                    })
                                    console.print(f"✅ Extraction succeeded: {len(extracted_text)} chars")
                                else:
                                    # Try alternate extraction method
                                    fallback_content = await fallback_scrape(url, debug)
                                    
                                    if fallback_content and len(fallback_content) > 100:
                                        extracted_text = fallback_content[:3000]  # Limit content size
                                        extracted_data.append({
                                            "title": title,
                                            "url": url,
                                            "content": extracted_text,
                                            "snippet": result.get('snippet', '')
                                        })
                                        console.print(f"✅ Extraction succeeded: {len(extracted_text)} chars")
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
                                
                                if fallback_content and len(fallback_content) > 100:
                                    extracted_text = fallback_content[:3000]  # Limit content size
                                    extracted_data.append({
                                        "title": title,
                                        "url": url,
                                        "content": extracted_text,
                                        "snippet": result.get('snippet', '')
                                    })
                                    console.print(f"✅ Extraction succeeded: {len(extracted_text)} chars")
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
            for result in selected_results:
                url = result['link']
                title = result['title']
                
                if not url:
                    continue
                
                if not fallback_only:  # Only show this message if we're not intentionally using fallback only
                    console.print(f"🌐 Fallback scraping: {title}")
                else:
                    console.print(f"🌐 Scraping: {title}")
                    
                try:
                    # Try fallback scraping
                    fallback_content = await fallback_scrape(url, debug)
                    
                    if fallback_content and len(fallback_content) > 100:
                        extracted_text = fallback_content[:3000]  # Limit content size
                        extracted_data.append({
                            "title": title,
                            "url": url,
                            "content": extracted_text,
                            "snippet": result.get('snippet', '')
                        })
                        console.print(f"✅ Extraction succeeded: {len(extracted_text)} chars")
                    else:
                        console.print(f"⚠️ No content extracted from: {title}")
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
    
    # Extract sources information for the LLM
    sources_info = ""
    for idx, data in enumerate(extracted_data, 1):
        sources_info += f"Source {idx}: {data['title']}\n"
        sources_info += f"URL: {data['url']}\n"
        sources_info += f"Content: {data['content'][:300]}...\n\n"
    
    # Create prompt for document generation
    if format == 'markdown':
        doc_template = """Create a comprehensive markdown document about this topic. Use proper markdown formatting with headings, subheadings, lists, and code blocks. 

For code blocks, use the following format:
```language_name
code goes here
```

Ensure there's an empty line before and after each code block. Always specify a language for syntax highlighting (e.g., ```bash, ```python, etc.).

For all markdown headings, use the following format:
# Main Title (H1)
## Section Title (H2)
### Subsection Title (H3)

When creating a Table of Contents, follow these formatting rules:
1. Include an anchor ID that exactly matches the heading text but converted to lowercase with spaces replaced by hyphens
2. Remove any special characters from anchor IDs (keep only letters, numbers, and hyphens)
3. Use this format for all TOC entries: [Exact Section Title](#lowercase-with-hyphens)

For example:
## Table of Contents
1. [Introduction](#introduction)
2. [Basic Commands](#basic-commands)
3. [Advanced Usage](#advanced-usage)
   - [Sub-Feature One](#sub-feature-one)
   - [Sub-Feature Two](#sub-feature-two)

Do not use bold formatting (**text**) for TOC entries - always use proper link syntax.

EXTREMELY IMPORTANT: Do NOT include ```markdown or ```anything at the beginning of the document. 
EXTREMELY IMPORTANT: Do NOT include ``` at the end of the document.
EXTREMELY IMPORTANT: Only use triple backticks for actual code blocks within the document, not for the document itself."""
    elif format == 'html':
        doc_template = "Create a comprehensive HTML document about this topic. Use proper HTML structure and tags."
    else:
        doc_template = "Create a comprehensive document about this topic in plain text format."
    
    # Add image instructions if we have images
    if image_data["images"] and (format == 'markdown' or format == 'html'):
        doc_template += f"""

Include {len(image_data['images'])} relevant image placeholders where appropriate in the content.
IMPORTANT: Use exactly these placeholder formats:
- For markdown: ![Image Description](IMAGE_{1}) for the first image, ![Image Description](IMAGE_{2}) for the second, etc.
- For HTML: <img src="IMAGE_{1}" alt="Image Description"> for the first image, etc.
"""
    
    # Build the full prompt
    prompt = f"""
    {doc_template}
    
    Topic: {query_str}
    
    Based on the following web research results, create a well-structured document that covers all important aspects of the topic.
    
    RESEARCH DATA:
    {sources_info}
    
    Make the document coherent, informative, and comprehensive.
    """
    
    console.print("🧠 Analyzing collected information...")
    
    # Get the LLM instance
    llm = get_llm()
    
    try:
        # Generate content - use professional mode for document generation
        professional_mode = write  # Use professional mode when generating a document
        response = asyncio.run(llm.generate_response(prompt, professional_mode=professional_mode))
        
        # Process the generated content to replace image placeholders
        if image_data["images"] and (format == 'markdown' or format == 'html'):
            print(f"Processing {len(image_data['images'])} images for document")
            
            for i, img_data in enumerate(image_data["images"]):
                # 1-indexed for placeholders
                img_idx = i + 1
                
                if format == 'markdown':
                    # Try to find patterns with IMAGE placeholder in various formats
                    img_placeholder_patterns = [
                        r'!\[([^\]]+)\]\(IMAGE_{}\)'.format(img_idx),  # ![Alt text](IMAGE_n)
                        r'!\[([^\]]+)\]!\[([^\]]+)\]\(/[^)]+\)'.format(img_idx),  # ![Alt]![Description](/path)
                        r'!\[([^\]]+)\]IMAGE_{}'.format(img_idx),  # ![Alt]IMAGE_n
                        r'!\[([^\]]+)\]\[IMAGE_{}\]'.format(img_idx),  # ![Alt][IMAGE_n]
                        r'\(IMAGE_{}\)'.format(img_idx),  # (IMAGE_n)
                        r'IMAGE_{}'.format(img_idx)  # IMAGE_n plain
                    ]
                    
                    # Format for Markdown
                    img_tag = format_image_for_markdown(
                        img_data["url"], 
                        img_data["alt_text"], 
                        img_data["width"]
                    )
                    
                    # First try these exact patterns
                    image_replaced = False
                    for pattern in img_placeholder_patterns:
                        print(f"Looking for pattern: {pattern}")
                        matches = re.finditer(pattern, response)
                        for match in matches:
                            image_replaced = True
                            full_match = match.group(0)
                            
                            # Get the alt text if available, or use a default
                            try:
                                alt_text = match.group(1) if match.lastindex and match.lastindex >= 1 else "Image"
                            except:
                                alt_text = "Image"
                                
                            # Create proper markdown image
                            proper_image = f"![{alt_text}]({img_data['url']})"
                            print(f"Replacing '{full_match}' with '{proper_image}'")
                            response = response.replace(full_match, proper_image)
                    
                    # If no pattern matched, fall back to simple replacement
                    if not image_replaced:
                        print(f"No complex patterns matched for image {img_idx}, trying simple replacements")
                        # Try simple replacements
                        replacements = [
                            (f"(IMAGE_{img_idx})", f"({img_data['url']})"),
                            (f"[IMAGE_{img_idx}]", f"[{img_data['url']}]"),
                            (f"IMAGE_{img_idx}", img_data["url"])
                        ]
                        
                        for old, new in replacements:
                            if old in response:
                                print(f"Replacing {old} with {new}")
                                response = response.replace(old, new)
                                image_replaced = True
                                break
                        
                    if not image_replaced:
                        print(f"Unable to find any placeholder for image {img_idx}")
                
                elif format == 'html':
                    # Format for HTML
                    img_tag = format_image_for_html(
                        img_data["url"], 
                        img_data["alt_text"], 
                        img_data["width"]
                    )
                    
                    # Primary placeholder format: src="IMAGE_{n}"
                    primary_placeholder = f"IMAGE_{img_idx}"
                    if primary_placeholder in response:
                        print(f"Replacing {primary_placeholder} with {img_data['url']}")
                        response = response.replace(primary_placeholder, img_data["url"])
                    else:
                        # Try to find <img src="IMAGE_n" patterns
                        img_html_pattern = r'<img[^>]*src=["\'](IMAGE_{})["\'][^>]*>'.format(img_idx)
                        matches = re.finditer(img_html_pattern, response)
                        img_replaced = False
                        for match in matches:
                            img_replaced = True
                            full_match = match.group(0)
                            # Replace just the src attribute
                            new_img_tag = full_match.replace(f'src="{primary_placeholder}"', f'src="{img_data["url"]}"')
                            response = response.replace(full_match, new_img_tag)
                            print(f"Replaced HTML img tag: {full_match} with {new_img_tag}")
                        
                        if not img_replaced:
                            print(f"Cannot find {primary_placeholder} in HTML, tried pattern: {img_html_pattern}")
            
            # Add credits at the end of the document
            if image_data["credits"]:
                if format == 'markdown':
                    response += "\n\n---\n\n## Image Credits\n\n"
                    for credit in image_data["credits"]:
                        response += f"* {credit}\n"
                else:
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
                base_filename = 'research_' + '_'.join(words) + ext
                # Use the docs/research directory for organization
                output_dir = get_docs_dir('research')
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
                    # Otherwise, put it in the docs/research directory
                    output_dir = get_docs_dir('research')
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
    <title>{query_str} - Research</title>
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
            console.print(f"✅ Research document saved to: {file_path}")
        else:
            # Display the response in terminal
            console.print("\n" + "=" * 60)
            console.print("📊 RESEARCH RESULTS")
            console.print("=" * 60)
            console.print(f"\n💡 {response}\n")
            console.print("=" * 60)
            console.print(f"Sources: {len(extracted_data)} websites analyzed")
            console.print("=" * 60)
        
        return 0  # Return success code
        
    except AttributeError as e:
        console.print("❌ Error: Provider not properly configured")
        return 1  # Return error code
    except Exception as e:
        console.print(f"❌ Error generating response: {str(e)}")
        return 1  # Return error code

if __name__ == "__main__":
    research()
