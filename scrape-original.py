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

# --- Structured Data Schema ---
class ScrapedData(BaseModel):
    title: str = Field(..., description="Title of the page.")
    description: str = Field(..., description="A detailed summary of the page content.")
    main_content: str = Field(..., description="Complete and comprehensive content of the page.")
    images: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Images extracted from the page.")

# --- Helper Functions ---
def is_same_domain(url1: str, url2: str) -> bool:
    return urlparse(url1).netloc == urlparse(url2).netloc

def is_relevant_content(text: str, topic: str = None) -> bool:
    """Check if extracted text is relevant to the topic with improved relevance scoring."""
    # If no topic provided, all content is relevant
    if not topic:
        return True
        
    topic_words = set(topic.lower().split())
    text_lower = text.lower()
    
    # Basic frequency counting
    word_count = 0
    for word in topic_words:
        word_count += text_lower.count(word)
    
    # Weighted by position (earlier mentions matter more)
    position_score = 0
    for word in topic_words:
        pos = text_lower.find(word)
        if pos != -1:
            # Earlier positions get higher scores
            position_score += max(0, 1.0 - (pos / min(1000, len(text_lower))))
    
    # Density score (relevant words per total length)
    density = word_count / max(1, len(text_lower.split()))
    
    # Combined score
    relevance_score = (0.5 * word_count) + (0.3 * position_score) + (0.2 * density * 100)
    
    # For debugging
    if "CLICHE_DEBUG" in os.environ:
        click.echo(f"Relevance score: {relevance_score} (threshold: 0.2)")
        click.echo(f"Word count: {word_count}, Position score: {position_score}, Density: {density}")
    
    return relevance_score > 0.2  # Lower threshold for relevance from 0.5 to 0.2

def is_url_relevant(url: str, topic: str = None) -> bool:
    """Check if URL seems relevant to the topic based on its text."""
    # If no topic provided, all URLs are relevant
    if not topic:
        return True
        
    # Extract words from URL path
    path_words = urlparse(url).path.lower().replace('-', ' ').replace('_', ' ').replace('/', ' ').split()
    
    # Check for topic words in URL path
    topic_words = set(topic.lower().split())
    matches = sum(1 for word in path_words if any(topic_word in word for topic_word in topic_words))
    
    return matches > 0

def is_wikipedia_url(url: str) -> bool:
    """Check if a URL is from Wikipedia."""
    return "wikipedia.org" in url.lower()

def is_python_org_url(url: str) -> bool:
    """Check if a URL is from Python.org."""
    parsed_url = urlparse(url)
    return parsed_url.netloc.lower() in ["python.org", "www.python.org", "docs.python.org"]

# --- Scraping Logic ---
async def scrape_page(crawler, url, base_url, visited, topic=None, include_images=False, max_images=10, min_image_size=100, image_dir=None):
    """Scrape a page and return structured data if relevant."""
    try:
        # Check if it's a special page that needs custom handling
        if is_wikipedia_url(url):
            click.echo("📚 Using specialized Wikipedia extraction")
            result = await extract_wikipedia_directly(url, topic, include_images, max_images, min_image_size, image_dir)
            return result

        # Check for Python.org pages which need specialized extraction
        if is_python_org_url(url):
            click.echo("DEBUG: Using specialized Python.org extraction")
            result = await extract_python_org_directly(url, topic, include_images, max_images, min_image_size, image_dir)
            return result
            
        config = CrawlerRunConfig(
            page_timeout=60000,
            wait_until='load',
            scan_full_page=True,
            magic=False,
            word_count_threshold=100,  # Increased threshold for more substantive pages
        )
        
        # First get the raw content
        click.echo(f"🔍 Crawling content from {url} with crawl4ai...")
        result = await crawler.arun(url=url, config=config)
        if not result or not result.cleaned_html:
            click.echo(f"⚠️ Failed to fetch content from {url}")
            return None, []
            
        # Check if no_llm is set in environment
        use_llm = "CLICHE_NO_LLM" not in os.environ
        
        # Try to use crawl4ai's extraction first
        extracted_data = None
        
        # Extract main content using BeautifulSoup if crawl4ai doesn't provide enough
        soup = BeautifulSoup(result.cleaned_html, 'lxml')
        
        # Remove unwanted elements
        for element in soup.select('nav, header, footer, .sidebar, .ads, script, style, iframe, form'):
            element.decompose()
            
        # Get the main content - try multiple strategies
        main_content = None
        for selector in ['main article', 'main', 'article', '.main-content', '#content', '.content', '[role="main"]', '.post-content', '.entry-content', '.page-content']:
            main_content = soup.select_one(selector)
            if main_content and len(str(main_content)) > 500:  # Must be substantial content
                break
                
        # If no main content found, try to get the largest content block
        if not main_content:
            content_blocks = []
            for tag in soup.find_all(['div', 'section', 'article']):
                # Skip if it's likely navigation or sidebar
                if any(cls in (tag.get('class', []) or []) for cls in ['nav', 'menu', 'sidebar', 'footer']):
                    continue
                content_blocks.append((len(str(tag)), tag))
            if content_blocks:
                main_content = max(content_blocks, key=lambda x: x[0])[1]
            
        if not main_content:
            main_content = soup.body
            
        if not main_content:
            return None, []
            
        # Get the page title
        title = soup.title.get_text() if soup.title else url.split('/')[-1]
        
        # Extract images if requested
        extracted_images = []
        if include_images and main_content:
            # Extract and download images
            click.echo(f"🖼️ Extracting images from {url}...")
            try:
                # Use the cleaned HTML content from the main content area
                main_html = str(main_content)
                
                # Use the async-safe version when we're already in an async context
                print(f"DEBUG: Using async-safe image extraction for {url}")
                scraped_images = await extract_and_download_images_async(
                    main_html, 
                    url, 
                    max_images=max_images, 
                    min_size=min_image_size,
                    output_dir=Path(image_dir) if image_dir else None,
                    topic=topic  # Pass the topic parameter
                )
                
                if scraped_images:
                    click.echo(f"📸 Downloaded {len(scraped_images)} images from {url}")
                    extracted_images = [img.to_dict() for img in scraped_images]
                    # Print debug info about extracted images
                    print(f"DEBUG: Extracted {len(extracted_images)} image data entries")
                    for idx, img in enumerate(extracted_images):
                        print(f"DEBUG: Image {idx+1}: URL={img.get('url')}, local_path={img.get('local_path')}")
                else:
                    click.echo(f"ℹ️ No images found or downloaded from {url}")
            except Exception as e:
                click.echo(f"⚠️ Error extracting images from {url}: {str(e)}")
                import traceback
                print(f"DEBUG: Image extraction error details: {traceback.format_exc()}")
                
        # Clean up the content
        for tag in main_content.find_all(['a', 'img']):
            # Convert relative URLs to absolute
            if 'href' in tag.attrs:
                tag['href'] = urljoin(url, tag['href'])
            if 'src' in tag.attrs:
                tag['src'] = urljoin(url, tag['src'])
                
        # Default to BeautifulSoup extraction if LLM is disabled
        if not use_llm:
            click.echo("📄 Using non-LLM extraction method (LLM disabled)")
            # Convert HTML to markdown-like content
            content_text = ""
            
            # First attempt to extract the main outline by getting all headings
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            has_structure = len(headings) > 1

            # Create a map of heading levels for more consistent structure
            heading_map = {}
            for idx, h_tag in enumerate(headings):
                level = int(h_tag.name[1])
                heading_map[h_tag] = level
                
            # If page has structured headings, extract content section by section
            if has_structure:
                click.echo(f"📑 Found {len(headings)} headings for structured extraction")
                
                # Extract all content based on headings
                for idx, h_tag in enumerate(headings):
                    heading_level = heading_map[h_tag]
                    heading_text = h_tag.get_text(strip=True)
                    content_text += f"{'#' * heading_level} {heading_text}\n\n"
                    
                    # Get all content until next heading of same or higher level
                    current = h_tag.next_sibling
                    while current:
                        # Stop if we hit another heading of same or higher level
                        if (hasattr(current, 'name') and 
                            current.name and 
                            current.name.startswith('h') and
                            current.name[1].isdigit() and
                            int(current.name[1]) <= heading_level):
                            break
                            
                        # Process this element
                        if hasattr(current, 'name') and current.name:
                            if current.name == 'p':
                                text = current.get_text(strip=True)
                                if text:
                                    content_text += f"{text}\n\n"
                            elif current.name in ['ul', 'ol']:
                                for li in current.find_all('li', recursive=True):
                                    li_text = li.get_text(strip=True)
                                    if li_text:
                                        content_text += f"* {li_text}\n"
                                content_text += "\n"
                            elif current.name in ['pre', 'code']:
                                # Enhanced code block handling with language detection
                                process_code_block(current, content_text)
                            elif current.name == 'table':
                                # Extract table content
                                content_text += extract_table_as_markdown(current) + "\n\n"
                            elif current.name == 'div':
                                # Recursively process div content
                                div_content = process_div_content(current)
                                if div_content:
                                    content_text += div_content + "\n\n"
                                
                        # Move to next element
                        current = current.next_sibling
            else:
                # No structured headings found, extract all content in sequence
                click.echo("📑 No structured headings found, extracting all content")
                
                # Extract title as a heading if available
                if title:
                    content_text += f"# {title}\n\n"
                
                # Extract all paragraphs and other content elements
                for element in main_content.find_all(['p', 'ul', 'ol', 'pre', 'code', 'table', 'div']):
                    # Skip elements that are part of navigation or non-content areas
                    if any(cls in (element.get('class', []) or []) for cls in ['nav', 'menu', 'sidebar', 'footer']):
                        continue
                        
                    if element.name == 'p':
                        text = element.get_text(strip=True)
                        if text:
                            content_text += f"{text}\n\n"
                    elif element.name in ['ul', 'ol']:
                        for li in element.find_all('li', recursive=True):
                            li_text = li.get_text(strip=True)
                            if li_text:
                                content_text += f"* {li_text}\n"
                        content_text += "\n"
                    elif element.name in ['pre', 'code']:
                        # Enhanced code block handling
                        process_code_block(element, content_text)
                    elif element.name == 'table':
                        # Extract table content
                        content_text += extract_table_as_markdown(element) + "\n\n"
                    elif element.name == 'div' and element.find(['p', 'ul', 'ol', 'pre', 'code'], recursive=False):
                        # Only process divs that directly contain content elements
                        div_content = process_div_content(element)
                        if div_content:
                            content_text += div_content + "\n\n"
            
            # Create a basic description
            description = ""
            for p in main_content.find_all('p')[:5]:  # Increased to first 5 paragraphs for better descriptions
                description += p.get_text(strip=True) + " "
            
            # Check if content is relevant to topic
            if not is_relevant_content(content_text, topic):
                return None, result.links or []
            
            # Structure the data
            bs_data = {
                "title": title or "Untitled",
                "description": description[:500] + "..." if len(description) > 500 else description,
                "main_content": content_text,
                "url": url
            }
            
            # Add images to the bs_data if any
            if extracted_images:
                print(f"DEBUG: Adding {len(extracted_images)} images to BeautifulSoup data")
                bs_data["images"] = extracted_images
            
            click.echo(f"✅ Extracted {len(content_text)} characters of content with BeautifulSoup method")
            return bs_data, result.links or []
        
        # If we're here, we'll try using the LLM extraction
        # Prepare a prompt for direct LLM usage
        topic_str = f"about '{topic}'" if topic else "from this web page"
        prompt = f"""
You are a data extraction system that ONLY outputs valid JSON. You never add explanatory text. You only output correctly formatted JSON data structures.

INSTRUCTIONS:
Extract structured data {topic_str} and return ONLY a valid JSON object.

OUTPUT FORMAT: 
You MUST follow these rules EXACTLY without exception:
1. Return ONLY a valid JSON object - no explanations, no intros, no markdown
2. Do NOT start with phrases like "Here's the JSON:", "Here's the data:", or "Certainly!"
3. Do NOT wrap the JSON in code fences (```)
4. Start your output with the opening brace {{
5. End your output with the closing brace }}
6. All JSON field names must be in double quotes
7. All string values must be in double quotes with proper escaping
8. Never explain your output or add notes before or after the JSON

JSON FIELDS TO INCLUDE:
- "title": {title if title else 'The main title of the article'}
- "description": A detailed summary (100-200 words) of what the article covers
- "main_content": The complete content of the article with proper markdown formatting

CONTENT EXTRACTION REQUIREMENTS:
1. Extract the COMPLETE article content, not just a summary
2. Include ALL code examples, tables, and technical specifications
3. Preserve ALL headings, subheadings and section structure
4. Include ALL relevant diagrams, charts, and visuals (described in markdown)
5. Capture the FULL technical depth and breadth of the content
6. Do not skip or summarize sections - extract EVERYTHING
7. Include ALL lists, bullet points, and enumerated items
8. Retain ALL technical terminology and jargon
9. Keep code samples exactly as they appear without simplification
10. Maintain tables with their full content and structure

When including code blocks in the main_content field, follow this exact format:

```python
# Example code with proper formatting
def hello():
    print("Hello, world!")
    return True
```

CORRECT RESPONSE EXAMPLE (start your response exactly like this):
{{
  "title": "Article Title",
  "description": "A detailed summary of the content...",
  "main_content": "# Main Heading\\n\\nContent here..."
}}

HTML CONTENT TO EXTRACT:
{str(main_content)[:20000]}  # Increased limit to capture more content
"""

        click.echo(f"🔄 Extracting content with LLM from {url}")
        
        # Flag to track if we need to fall back to non-LLM extraction
        use_fallback = False
        
        # Get the LLM instance
        try:
            llm = get_llm()
            print(f"DEBUG: Successfully created LLM instance with provider: {llm.__class__.__name__}")
        except Exception as e:
            click.echo(f"⚠️ Error creating LLM instance: {str(e)}")
            print(f"DEBUG: Falling back to non-LLM extraction due to LLM creation error")
            use_fallback = True
        
        # Initialize extracted_data
        extracted_data = None
        
        if use_fallback:
            # Early fallback due to LLM creation error
            click.echo("📄 Using non-LLM extraction method for comprehensive content extraction")
            # ... let the code fall through to the fallback extraction below ...
        else:
            # Create a function to run the LLM in a separate thread to avoid event loop issues
            def run_llm_in_thread():
                import threading
                result = {"success": False, "data": None, "error": None}
                
                def thread_func():
                    try:
                        nonlocal result
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Run the LLM extraction in the new event loop
                        extraction_result = loop.run_until_complete(
                            extract_with_llm(
                                url, 
                                html_content, 
                                depth=depth, 
                                headers=headers,
                                max_tokens=8000
                            )
                        )
                        
                        result["success"] = True
                        result["data"] = extraction_result
                        loop.close()
                    except Exception as e:
                        result["error"] = str(e)
                        print(f"🔴 LLM extraction failed: {e}")
                        # After an error, fall back to standard extraction
                
                # Start the thread
                thread = threading.Thread(target=thread_func)
                thread.start()
                thread.join(timeout=120)  # Wait for 120 seconds or until the thread completes
                
                return result
            
            # Run the LLM in a separate thread
            llm_result = run_llm_in_thread()
            
            if llm_result["success"] and llm_result["data"]:
                # Use the LLM extraction if it was successful
                extraction_result = llm_result["data"]
                if extraction_result:
                    # Check if the extraction_result is a dict with the expected keys
                    if isinstance(extraction_result, dict) and "title" in extraction_result:
                        main_content = extraction_result.get("main_content", "")
                        
                        if main_content and len(main_content) > 100:
                            print(f"✅ LLM extraction success with {len(main_content)} chars")
                            # Continue with the LLM extraction
                            use_fallback = False
                            title = extraction_result.get("title", "")
                            description = extraction_result.get("description", "")
                        else:
                            print("🔴 LLM extraction returned empty or insufficient content, falling back to standard extraction")
                            use_fallback = True
                    else:
                        print("🔴 LLM extraction returned invalid data format, falling back to standard extraction")
                        use_fallback = True
                else:
                    print("🔴 LLM extraction returned no data, falling back to standard extraction")
                    use_fallback = True
            else:
                error = llm_result.get("error", "unknown error")
                print(f"🔴 LLM extraction failed: {error}")
                use_fallback = True
        
        # Use the fallback extraction method if needed
        if use_fallback:
            # Convert HTML to markdown-like content
            content_text = ""
            
            # First attempt to extract the main outline by getting all headings
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            has_structure = len(headings) > 1

            # Create a map of heading levels for more consistent structure
            heading_map = {}
            for idx, h_tag in enumerate(headings):
                level = int(h_tag.name[1])
                heading_map[h_tag] = level
                
            # If page has structured headings, extract content section by section
            if has_structure:
                click.echo(f"📑 Found {len(headings)} headings for structured extraction")
                
                # Extract all content based on headings
                for idx, h_tag in enumerate(headings):
                    heading_level = heading_map[h_tag]
                    heading_text = h_tag.get_text(strip=True)
                    content_text += f"{'#' * heading_level} {heading_text}\n\n"
                    
                    # Get all content until next heading of same or higher level
                    current = h_tag.next_sibling
                    while current:
                        # Stop if we hit another heading of same or higher level
                        if (hasattr(current, 'name') and 
                            current.name and 
                            current.name.startswith('h') and
                            current.name[1].isdigit() and
                            int(current.name[1]) <= heading_level):
                            break
                            
                        # Process this element
                        if hasattr(current, 'name') and current.name:
                            if current.name == 'p':
                                text = current.get_text(strip=True)
                                if text:
                                    content_text += f"{text}\n\n"
                            elif current.name in ['ul', 'ol']:
                                for li in current.find_all('li', recursive=True):
                                    li_text = li.get_text(strip=True)
                                    if li_text:
                                        content_text += f"* {li_text}\n"
                                content_text += "\n"
                            elif current.name in ['pre', 'code']:
                                # Enhanced code block handling with language detection
                                process_code_block(current, content_text)
                            elif current.name == 'table':
                                # Extract table content
                                content_text += extract_table_as_markdown(current) + "\n\n"
                            elif current.name == 'div':
                                # Recursively process div content
                                div_content = process_div_content(current)
                                if div_content:
                                    content_text += div_content + "\n\n"
                                
                        # Move to next element
                        current = current.next_sibling
            else:
                # No structured headings found, extract all content in sequence
                click.echo("📑 No structured headings found, extracting all content")
                
                # Extract title as a heading if available
                if title:
                    content_text += f"# {title}\n\n"
                
                # Extract all paragraphs and other content elements
                for element in main_content.find_all(['p', 'ul', 'ol', 'pre', 'code', 'table', 'div']):
                    # Skip elements that are part of navigation or non-content areas
                    if any(cls in (element.get('class', []) or []) for cls in ['nav', 'menu', 'sidebar', 'footer']):
                        continue
                        
                    if element.name == 'p':
                        text = element.get_text(strip=True)
                        if text:
                            content_text += f"{text}\n\n"
                    elif element.name in ['ul', 'ol']:
                        for li in element.find_all('li', recursive=True):
                            li_text = li.get_text(strip=True)
                            if li_text:
                                content_text += f"* {li_text}\n"
                        content_text += "\n"
                    elif element.name in ['pre', 'code']:
                        # Enhanced code block handling
                        process_code_block(element, content_text)
                    elif element.name == 'table':
                        # Extract table content
                        content_text += extract_table_as_markdown(element) + "\n\n"
                    elif element.name == 'div' and element.find(['p', 'ul', 'ol', 'pre', 'code'], recursive=False):
                        # Only process divs that directly contain content elements
                        div_content = process_div_content(element)
                        if div_content:
                            content_text += div_content + "\n\n"
            
            # Create a basic description
            description = ""
            for p in main_content.find_all('p')[:5]:  # Increased to first 5 paragraphs for better descriptions
                description += p.get_text(strip=True) + " "
            
            # Check if content is relevant to topic
            if not is_relevant_content(content_text, topic):
                return None, result.links or []
            
            # Structure the data
            fallback_data = {
                "title": title or "Untitled",
                "description": description[:500] + "..." if len(description) > 500 else description,
                "main_content": content_text,
                "url": url
            }
            
            # Add images to the fallback data if any
            if extracted_images:
                print(f"DEBUG: Adding {len(extracted_images)} images to fallback data")
                fallback_data["images"] = extracted_images
            
            click.echo(f"✅ Extracted {len(content_text)} characters of content with non-LLM method")
            return fallback_data, result.links or []
        else:
            # If we made it here, LLM extraction was successful
            click.echo(f"✅ Successfully extracted content using LLM")
            
            # Make sure main_content is set
            if "main_content" not in extracted_data and "content" in extracted_data:
                # Handle the case where content is provided but not in main_content
                content_value = extracted_data.get("content", "")
                
                # If content is a dictionary, we need to serialize it to text
                if isinstance(content_value, dict):
                    content_text = ""
                    # Convert the structured content dict to markdown format
                    for section_name, section_content in content_value.items():
                        content_text += f"# {section_name.replace('_', ' ').title()}\n\n"
                        
                        if isinstance(section_content, list):
                            for item in section_content:
                                if isinstance(item, dict):
                                    for subsection, text in item.items():
                                        content_text += f"## {subsection.replace('_', ' ').title()}\n\n"
                                        content_text += f"{text}\n\n"
                                else:
                                    content_text += f"* {item}\n"
                            content_text += "\n"
                        else:
                            content_text += f"{section_content}\n\n"
                            
                    extracted_data["main_content"] = content_text
                else:
                    # If content is already a string, just assign it
                    extracted_data["main_content"] = content_value
            elif "main_content" not in extracted_data:
                # Create a fallback main_content if none exists
                extracted_data["main_content"] = extracted_data.get("description", "")
            
            # Add images to the extracted data if any
            if extracted_images:
                print(f"DEBUG: Adding {len(extracted_images)} images to extracted data")
                extracted_data["images"] = extracted_images
            
            if not is_relevant_content(extracted_data.get("main_content", ""), topic):
                return None, result.links or []
                
            return extracted_data, result.links or []
    
    except Exception as e:
        click.echo(f"⚠️ Error during scraping: {str(e)}")
        import traceback
        click.echo(f"Debug details: {traceback.format_exc()}")
        return None, []

async def extract_wikipedia_directly(url, topic=None, include_images=False, max_images=10, min_image_size=100, image_dir=None):
    """Extract content from Wikipedia pages using direct requests."""
    try:
        # Use a proper user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml'
        }
        
        click.echo(f"🌐 Directly fetching Wikipedia page: {url}")
        # Add a debug message to show we're bypassing crawl4ai for Wikipedia
        print(f"DEBUG: Bypassing crawl4ai for direct Wikipedia extraction")
        
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        
        # Parse the HTML
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Get the title
        title_elem = soup.select_one("h1#firstHeading")
        if not title_elem:
            title_elem = soup.select_one("h1")
        title = title_elem.get_text(strip=True) if title_elem else "Wikipedia Article"
        click.echo(f"📄 Found title: {title}")
        
        # Get the content div
        content_div = soup.select_one("div.mw-parser-output")
        if not content_div:
            click.echo("⚠️ Could not find main content div. Searching alternatives...")
            # Try to find content in main content area
            main_content_div = soup.select_one("#mw-content-text")
            if main_content_div:
                content_div = main_content_div
        
        if not content_div:
            click.echo("❌ Failed to extract Wikipedia content structure")
            return None, []
        
        # Extract images if requested
        extracted_images = []
        if include_images and content_div:
            click.echo(f"🖼️ Extracting images from Wikipedia page...")
            try:
                # Instead of using asyncio.run, let's manually extract and download images
                content_html = str(content_div)
                # Use async-safe version of the image extractor and pass topic
                scraped_images = await extract_and_download_images_async(
                    content_html,
                    url,
                    max_images=max_images,
                    min_size=min_image_size,
                    output_dir=Path(image_dir) if image_dir else None,
                    topic=topic  # Pass the topic parameter for better organization
                )
                
                if scraped_images:
                    click.echo(f"📸 Downloaded {len(scraped_images)} images from Wikipedia")
                    extracted_images = [img.to_dict() for img in scraped_images]
                    print(f"DEBUG: Extracted {len(extracted_images)} Wikipedia image entries")
                else:
                    click.echo(f"ℹ️ No images found or downloaded from Wikipedia page")
                
            except Exception as e:
                click.echo(f"⚠️ Error extracting images from Wikipedia: {str(e)}")
                import traceback
                print(f"DEBUG: Wikipedia image extraction error: {traceback.format_exc()}")
        
        # Get the description from the first paragraph
        description = ""
        first_para = None
        
        # Wikipedia often has empty paragraph elements, so we need to find the first real one
        for p in content_div.select("p"):
            if p.get_text(strip=True) and not 'mw-empty-elt' in p.get('class', []):
                first_para = p
                break
                
        if first_para:
            description = first_para.get_text(strip=True)
            click.echo(f"📄 Found description: {description[:100]}...")
        
        # Extract the main content
        main_content = ""
        link_targets = []
        
        # Process each direct child of the content div
        for element in content_div.children:
            # Skip empty elements or those without names
            if not element.name:
                continue
                
            # Skip non-content elements
            skip_classes = ['toc', 'thumb', 'navbox', 'reflist', 'refbegin', 'metadata', 'catlinks']
            if element.get('class') and any(cls in str(element.get('class')) for cls in skip_classes):
                continue
                
            # Handle headings
            if element.name.startswith('h') and len(element.name) == 2 and element.name[1].isdigit():
                heading_level = int(element.name[1])
                heading_text = element.get_text(strip=True)
                main_content += f"{'#' * heading_level} {heading_text}\n\n"
            
            # Handle paragraphs
            elif element.name == 'p':
                para_text = element.get_text(strip=True)
                if para_text:
                    main_content += f"{para_text}\n\n"
                    
            # Handle lists (both ordered and unordered)
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li', recursive=True):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        main_content += f"* {li_text}\n"
                main_content += "\n"
            
            # Handle code blocks and pre-formatted text
            elif element.name in ['pre', 'code']:
                code_text = element.get_text()
                # Detect language if possible
                language = "text"  # Default language
                if 'class' in element.attrs:
                    classes = element['class']
                    for cls in classes:
                        if cls.startswith('language-'):
                            language = cls.replace('language-', '')
                        elif cls in ['python', 'javascript', 'java', 'cpp', 'csharp', 'html', 'css', 'bash', 'sql']:
                            language = cls
                
                # Try to detect Python syntax
                if language == "text" and ('def ' in code_text or 'import ' in code_text or 
                                     'class ' in code_text or '#' in code_text or
                                     'print(' in code_text or 'for ' in code_text and 'in ' in code_text):
                    language = "python"
                
                # Format the code block with proper fences and language
                main_content += f"```{language}\n{code_text}\n```\n\n"
                
            # Handle div elements that might contain content
            elif element.name == 'div':
                # Skip specific div types
                if element.get('class') and any(cls in str(element.get('class')) for cls in skip_classes):
                    continue
                    
                # Check if this might be a code block
                is_code_block = False
                language = "text"
                
                if 'class' in element.attrs:
                    classes = element['class']
                    code_block_classes = ['code', 'code-block', 'highlight', 'syntax', 'example']
                    for cls in classes:
                        if any(code_cls in str(cls).lower() for code_cls in code_block_classes):
                            is_code_block = True
                        if isinstance(cls, str) and cls.startswith('language-'):
                            language = cls.replace('language-', '')
                        elif isinstance(cls, str) and cls in ['python', 'javascript', 'java', 'cpp', 'csharp', 'html', 'css', 'bash', 'sql']:
                            language = cls
                
                # Check if it contains a pre or code tag
                code_tag = element.find(['pre', 'code'])
                if code_tag:
                    is_code_block = True
                    code_text = code_tag.get_text()
                    
                    # Try to detect Python syntax
                    if language == "text" and ('def ' in code_text or 'import ' in code_text or 
                                         'class ' in code_text or '#' in code_text or
                                         'print(' in code_text or 'for ' in code_text and 'in ' in code_text):
                        language = "python"
                        
                    # Format the code block with proper fences and language
                    main_content += f"```{language}\n{code_text}\n```\n\n"
                elif is_code_block:
                    # It's marked as code but doesn't have explicit code tags
                    code_text = element.get_text()
                    main_content += f"```{language}\n{code_text}\n```\n\n"
                else:
                    # Process paragraphs within divs
                    for p in element.find_all('p', recursive=False):
                        p_text = p.get_text(strip=True)
                        if p_text:
                            main_content += f"{p_text}\n\n"
                    
                    # Process lists within divs
                    for lst in element.find_all(['ul', 'ol'], recursive=False):
                        for li in lst.find_all('li'):
                            content_text += f"* {li.get_text(strip=True)}\n"
                        main_content += "\n"
            
            # Extract links for further crawling
            for a in element.find_all('a', href=True):
                href = a.get('href', '')
                if href.startswith('/wiki/') and ':' not in href:  # Skip special pages
                    full_url = 'https://en.wikipedia.org' + href
                    link_targets.append(full_url)
        
        # For Wikipedia, we SKIP the topic relevance check entirely or make it more lenient
        # Wikipedia URLs are already topic-specific based on their structure
        if topic:
            # If a topic is specified, we do a more lenient check than for other websites
            # We'll just make sure some aspect of the topic appears somewhere in the content            
            topic_words = set(topic.lower().split('_'))
            text_lower = main_content.lower()
            
            # Check if any of the topic words appear anywhere in the content
            found_any_topic_word = any(word in text_lower for word in topic_words)
            
            if not found_any_topic_word:
                # If we couldn't find any topic words, check in the Wikipedia title too
                title_lower = title.lower()
                found_in_title = any(word in title_lower for word in topic_words)
                
                if not found_in_title:
                    click.echo(f"⚠️ Wikipedia content doesn't seem related to topic '{topic}'")
                    # Despite the warning, we'll still return the content for Wikipedia pages
        
        # Create data structure
        wiki_data = {
            "title": title,
            "description": description[:500] + "..." if len(description) > 500 else description,
            "main_content": main_content,
            "url": url
        }
        
        # Add images to wiki data if any were extracted
        if extracted_images:
            print(f"DEBUG: Adding {len(extracted_images)} images to Wikipedia data")
            wiki_data["images"] = extracted_images
        
        click.echo(f"✅ Extracted {len(main_content)} characters of Wikipedia content")
        return wiki_data, link_targets
        
    except Exception as e:
        click.echo(f"❌ Error in direct Wikipedia extraction: {str(e)}")
        import traceback
        click.echo(f"  Error details: {traceback.format_exc()}")
        return None, []

async def extract_python_org_directly(url, topic=None, include_images=False, max_images=10, min_image_size=100, image_dir=None):
    """Extract content from Python.org pages using direct requests with specialized parsing.
    
    Python.org has a unique structure that requires specific handling to extract content properly.
    """
    try:
        # Use a proper user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml'
        }
        
        # Add blue crawler initialization output for consistency with other scrapers
        click.secho("Creating AsyncWebCrawler instance...", fg="blue", bold=True)
        click.secho("Using specialized extraction method for Python.org...", fg="blue", bold=True)
        
        click.echo(f"🌐 Directly fetching Python.org page: {url}")
        print(f"DEBUG: Using specialized Python.org extraction")
        
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        
        # Parse the HTML
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Get the page title
        title = soup.title.get_text() if soup.title else "Python.org"
        click.echo(f"📄 Found title: {title}")
        
        # Extract the main content
        main_content = ""
        description = ""
        
        # Try to use crawl4ai for better extraction if available
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
            print(f"DEBUG: Attempting to use crawl4ai for enhanced extraction")
            
            crawler = AsyncWebCrawler()
            config = CrawlerRunConfig(
                page_timeout=60000,
                wait_until='load',
                scan_full_page=True,
                magic=True,  # Enable magic for better extraction
                word_count_threshold=50
            )
            
            # Create a function to run the crawler in a separate thread to avoid event loop issues
            def run_crawler_in_thread():
                result = {"success": False, "data": None, "error": None}
                
                def thread_func():
                    try:
                        nonlocal result
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Run the crawler in the new event loop
                        crawler_result = loop.run_until_complete(
                            crawler.arun(url=url, config=config)
                        )
                        
                        result["success"] = True
                        result["data"] = crawler_result
                        loop.close()
                    except Exception as e:
                        result["error"] = str(e)
                        print(f"🔴 crawl4ai extraction failed: {e}")
                
                # Start the thread
                thread = threading.Thread(target=thread_func)
                thread.start()
                thread.join(timeout=60)  # Wait for 60 seconds or until the thread completes
                
                return result
            
            # Run crawl4ai in a separate thread
            crawler_result = run_crawler_in_thread()
            
            # If crawl4ai extraction was successful, use it to enhance our content
            if crawler_result["success"] and crawler_result["data"]:
                print(f"DEBUG: Successfully used crawl4ai for enhanced extraction")
                result_data = crawler_result["data"]
                
                # Get title if not already set
                if result_data.title and not title:
                    title = result_data.title
                
                # Get main content from crawl4ai result
                if result_data.extracted_text:
                    # This will be our main fallback content if we don't extract it otherwise
                    enhanced_content = result_data.extracted_text
                    print(f"DEBUG: Got {len(enhanced_content)} chars from crawl4ai extraction")
                    
                # Get additional metadata if available
                if hasattr(result_data, 'metadata') and result_data.metadata:
                    print(f"DEBUG: Got metadata from crawl4ai: {result_data.metadata}")
                    # Extract description from metadata if available
                    if 'description' in result_data.metadata:
                        description = result_data.metadata['description']
        except Exception as e:
            print(f"DEBUG: Error using crawl4ai for enhanced extraction: {str(e)}")
            print(f"DEBUG: Falling back to standard Python.org extraction")
            enhanced_content = None
            
        # Python.org has different layouts for different sections
        # Main site layout
        if "www.python.org" in url or url.endswith("python.org/"):
            # Handle the main Python.org site
            # Try to get the introduction paragraph
            intro_paragraph = soup.select_one(".introduction p")
            if intro_paragraph:
                description = intro_paragraph.get_text(strip=True)
                main_content += f"# {title}\n\n{description}\n\n"
            
            # Extract the main content from the welcome section
            welcome_section = soup.select_one(".welcome-to")
            if welcome_section:
                for p in welcome_section.select("p"):
                    main_content += f"{p.get_text(strip=True)}\n\n"
            
            # Extract content from each section on the page
            for section in soup.select("section, .row"):
                section_title = section.select_one("h1, h2, h3")
                section_id = section.get('id', '')
                
                # Skip sections that are just navigation
                if 'navigation' in section.get('class', []) or 'meta-navigation' in section.get('class', []):
                    continue
                
                if section_title:
                    section_title_text = section_title.get_text(strip=True)
                    main_content += f"## {section_title_text}\n\n"
                elif section_id:
                    # Use the ID as a section title if no heading is found
                    main_content += f"## {section_id.replace('-', ' ').title()}\n\n"
                
                # Extract all paragraphs in this section
                for p in section.select("p"):
                    p_text = p.get_text(strip=True)
                    if p_text:
                        main_content += f"{p_text}\n\n"
                
                # Extract all lists in this section
                for ul in section.select("ul, ol"):
                    for li in ul.select("li"):
                        li_text = li.get_text(strip=True)
                        if li_text:
                            main_content += f"* {li_text}\n"
                    main_content += "\n"
                
                # Extract any code blocks
                for pre in section.select("pre, code"):
                    code_text = pre.get_text()
                    if code_text:
                        main_content += f"```python\n{code_text}\n```\n\n"
            
            # Get the latest news
            news_section = soup.select_one("#news, .news")
            if news_section:
                main_content += "## Latest News\n\n"
                for item in news_section.select("li, .list-recent-events li"):
                    item_text = item.get_text(strip=True)
                    if item_text:
                        main_content += f"* {item_text}\n"
                main_content += "\n"
            
            # Get upcoming events
            events_section = soup.select_one("#events, .events")
            if events_section:
                main_content += "## Upcoming Events\n\n"
                for item in events_section.select("li, .list-recent-events li"):
                    item_text = item.get_text(strip=True)
                    if item_text:
                        main_content += f"* {item_text}\n"
                main_content += "\n"
            
            # Get success stories or use cases
            success_section = soup.select_one("#success-stories, .success-stories")
            if success_section:
                main_content += "## Success Stories\n\n"
                for story in success_section.select(".success-story"):
                    title = story.select_one("h3")
                    if title:
                        main_content += f"### {title.get_text(strip=True)}\n\n"
                    
                    # Extract text from the story
                    story_text = story.get_text(strip=True)
                    if story_text:
                        main_content += f"{story_text}\n\n"
            
            # Get Python use cases
            uses_section = soup.select_one("#community-section")
            if uses_section:
                main_content += "## Use Python For\n\n"
                for category in uses_section.select(".community-banner"):
                    title = category.select_one("h2, h3")
                    if title:
                        main_content += f"### {title.get_text(strip=True)}\n\n"
                    
                    # Extract links
                    for link in category.select("a"):
                        link_text = link.get_text(strip=True)
                        if link_text:
                            main_content += f"* {link_text}\n"
                    main_content += "\n"
        
        # Python docs layout
        elif "docs.python.org" in url:
            # Handle the Python docs site
            # Get the main content div
            main_div = soup.select_one("#content") or soup.select_one(".body") or soup.select_one(".document")
            
            if main_div:
                # Extract the first paragraph for description
                first_para = main_div.select_one("p")
                if first_para:
                    description = first_para.get_text(strip=True)
                
                # Process all headings and their content
                headings = main_div.select("h1, h2, h3, h4, h5, h6")
                
                # If headings exist, process each section
                if headings:
                    for h_tag in headings:
                        level = int(h_tag.name[1])
                        heading_text = h_tag.get_text(strip=True)
                        main_content += f"{'#' * level} {heading_text}\n\n"
                        
                        # Get content until next heading
                        current = h_tag.next_sibling
                        while current:
                            if current.name and current.name.startswith('h') and int(current.name[1]) <= level:
                                break
                                
                            if hasattr(current, 'name') and current.name:
                                if current.name == 'p':
                                    text = current.get_text(strip=True)
                                    if text:
                                        main_content += f"{text}\n\n"
                                elif current.name in ['ul', 'ol']:
                                    for li in current.select("li"):
                                        li_text = li.get_text(strip=True)
                                        if li_text:
                                            main_content += f"* {li_text}\n"
                                    main_content += "\n"
                                elif current.name in ['pre', 'code'] or 'highlight' in current.get('class', []):
                                    # Special handling for code blocks in Python docs
                                    code_text = current.get_text()
                                    
                                    # Try to determine the language
                                    language = "python"  # Default for Python docs
                                    if 'class' in current.attrs:
                                        classes = current['class']
                                        for cls in classes:
                                            if isinstance(cls, str) and cls.startswith('language-'):
                                                language = cls.replace('language-', '')
                                                
                                    main_content += f"```{language}\n{code_text}\n```\n\n"
                                    
                            current = current.next_sibling
                else:
                    # If no headings, process the content sequentially
                    for element in main_div.children:
                        if hasattr(element, 'name') and element.name:
                            if element.name == 'p':
                                text = element.get_text(strip=True)
                                if text:
                                    main_content += f"{text}\n\n"
                            elif element.name in ['ul', 'ol']:
                                for li in element.select("li"):
                                    li_text = li.get_text(strip=True)
                                    if li_text:
                                        main_content += f"* {li_text}\n"
                                main_content += "\n"
                            elif element.name in ['pre', 'code'] or (hasattr(element, 'get') and 'highlight' in element.get('class', [])):
                                # Extract code
                                code_text = element.get_text()
                                main_content += f"```python\n{code_text}\n```\n\n"
            else:
                # Fallback if we can't find a main content div
                main_content = "# " + title + "\n\n"
                for p in soup.select("p"):
                    text = p.get_text(strip=True)
                    if text:
                        main_content += f"{text}\n\n"
        
        # Default handling for other Python.org pages
        else:
            # For other Python.org pages, extract content more generically
            content_elements = soup.select(".content p, .content ul, .content ol, .content pre, .content code, .content blockquote")
            
            # If we found content elements, process them
            if content_elements:
                main_content = "# " + title + "\n\n"
                
                for element in content_elements:
                    if element.name == 'p':
                        text = element.get_text(strip=True)
                        if text:
                            main_content += f"{text}\n\n"
                    elif element.name in ['ul', 'ol']:
                        for li in element.select("li"):
                            li_text = li.get_text(strip=True)
                            if li_text:
                                main_content += f"* {li_text}\n"
                        main_content += "\n"
                    elif element.name in ['pre', 'code']:
                        code_text = element.get_text()
                        main_content += f"```python\n{code_text}\n```\n\n"
                    elif element.name == 'blockquote':
                        quote_text = element.get_text(strip=True)
                        if quote_text:
                            main_content += f"> {quote_text}\n\n"
            else:
                # Last resort: just grab any content we can find
                main_content = "# " + title + "\n\n"
                for p in soup.select("p"):
                    text = p.get_text(strip=True)
                    if text:
                        main_content += f"{text}\n\n"
                
                # Try to find any lists
                for ul in soup.select("ul, ol"):
                    for li in ul.select("li"):
                        li_text = li.get_text(strip=True)
                        if li_text:
                            main_content += f"* {li_text}\n"
                    main_content += "\n"
        
        # If we have enhanced content from crawl4ai, use it to supplement our extraction
        if locals().get('enhanced_content') and len(main_content) < len(enhanced_content):
            print(f"DEBUG: Using enhanced content from crawl4ai ({len(enhanced_content)} chars vs {len(main_content)} chars)")
            main_content = enhanced_content
        
        # If we still don't have a description, create one from the first part of the content
        if not description and main_content:
            first_paragraph_match = re.search(r'# .*?\n\n(.*?)\n\n', main_content)
            if first_paragraph_match:
                description = first_paragraph_match.group(1)[:500]
            else:
                description = main_content[:500]
        
        # Add additional deep content extraction if we still don't have much
        if len(main_content) < 1000:
            print(f"DEBUG: Content is still short ({len(main_content)} chars), trying deeper extraction")
            
            # Look for main content containers
            main_containers = soup.select("main, article, .main-content, #content, .content, [role='main'], .body")
            for container in main_containers:
                container_content = ""
                
                # Extract all meaningful text from this container
                for element in container.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'pre', 'code', 'blockquote']):
                    if element.name.startswith('h') and len(element.name) == 2:
                        level = int(element.name[1])
                        heading_text = element.get_text(strip=True)
                        container_content += f"{'#' * level} {heading_text}\n\n"
                    elif element.name == 'p':
                        text = element.get_text(strip=True)
                        if text:
                            container_content += f"{text}\n\n"
                    elif element.name in ['ul', 'ol']:
                        for li in element.select("li"):
                            li_text = li.get_text(strip=True)
                            if li_text:
                                container_content += f"* {li_text}\n"
                        container_content += "\n"
                    elif element.name in ['pre', 'code']:
                        code_text = element.get_text()
                        container_content += f"```python\n{code_text}\n```\n\n"
                    elif element.name == 'blockquote':
                        quote_text = element.get_text(strip=True)
                        if quote_text:
                            container_content += f"> {quote_text}\n\n"
                
                # If this container has substantial content, use it
                if len(container_content) > len(main_content):
                    print(f"DEBUG: Found better content container with {len(container_content)} chars")
                    main_content = container_content
                    break
        
        # Create data structure
        structured_data = {
            "title": title,
            "description": description[:500] + "..." if len(description) > 500 else description,
            "main_content": main_content,
            "url": url
        }
        
        # Extract images if requested
        extracted_images = []
        if include_images:
            click.echo(f"🖼️ Extracting images from Python.org page...")
            images = []
            
            # Find all images with minimum size
            img_tags = soup.select("img")
            valid_images = []
            
            for img in img_tags:
                src = img.get('src')
                if not src:
                    continue
                    
                # Make relative URLs absolute
                if src.startswith('//'):
                    src = 'https:' + src
                elif not src.startswith('http'):
                    src = urljoin(url, src)
                    
                # Skip small images, icons, etc.
                if 'width' in img.attrs and int(img.attrs['width']) < min_image_size:
                    continue
                if 'height' in img.attrs and int(img.attrs['height']) < min_image_size:
                    continue
                    
                valid_images.append({
                    'url': src,
                    'alt_text': img.get('alt', ''),
                    'width': int(img.get('width', 0)) if img.get('width') else None,
                    'height': int(img.get('height', 0)) if img.get('height') else None
                })
                
                # Respect the max_images limit
                if len(valid_images) >= max_images:
                    break
            
            print(f"DEBUG: Found {len(valid_images)} Python.org images to download")
            
            # Create a subfolder for this Python.org scrape that will match the JSON filename pattern
            if not image_dir:
                base_dir = get_image_dir() / "scraped"
                domain = urlparse(url).netloc.replace('.', '_')
                
                # Create a folder name that will match the JSON filename pattern
                if topic:
                    subfolder = f"scraped_{domain}_{topic}"
                else:
                    subfolder = f"scraped_{domain}"
                
                # Add timestamp to ensure uniqueness
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = base_dir / f"{subfolder}_{timestamp}"
                print(f"DEBUG: Created organized subfolder for Python.org images: {output_dir}")
            else:
                output_dir = Path(image_dir)
            
            # Create the directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Download images
            for idx, img_data in enumerate(valid_images):
                try:
                    img_url = img_data['url']
                    print(f"DEBUG: Downloading Python.org image {idx+1}/{len(valid_images)}: {img_url}")
                    
                    # Extract filename from URL or create a hash-based name
                    parsed_url = urlparse(img_url)
                    filename = os.path.basename(parsed_url.path)
                    if not re.match(r'.*\.(jpg|jpeg|png|gif|webp|svg)$', filename, re.IGNORECASE):
                        # Create a hash-based filename
                        url_hash = hashlib.md5(img_url.encode()).hexdigest()[:10]
                        filename = f"python_org_image_{url_hash}.png"  # Default to PNG for Python.org
                    
                    # Save the image
                    output_path = output_dir / filename
                    response = requests.get(img_url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(response.content)
                            
                        # Determine file type from Content-Type header
                        content_type = response.headers.get('Content-Type', '')
                        file_type = None
                        if 'image/' in content_type:
                            file_type = content_type.split('/')[-1].split(';')[0]
                        
                        # Add to images list
                        image_data = {
                            'url': img_url,
                            'alt_text': img_data['alt_text'],
                            'caption': '',
                            'width': img_data['width'],
                            'height': img_data['height'],
                            'position_index': idx,
                            'source_url': url,
                            'local_path': str(output_path),
                            'file_type': file_type or 'png'
                        }
                        
                        images.append(image_data)
                        print(f"DEBUG: Successfully saved Python.org image {idx+1}")
                except Exception as e:
                    print(f"DEBUG: Error downloading Python.org image: {str(e)}")
            
            click.echo(f"📸 Downloaded {len(images)} images from Python.org")
            if images:
                click.echo(f"📂 Images saved to {output_dir}")
            print(f"DEBUG: Adding {len(images)} images to Python.org data")
            
            # Add images to structured data
            structured_data["images"] = images

        # Return the extracted data and an empty links list for consistency
        return structured_data, []
        
    except Exception as e:
        click.echo(f"⚠️ Error extracting content from Python.org: {str(e)}")
        import traceback
        print(f"DEBUG: Python.org extraction error: {traceback.format_exc()}")
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

@click.command()
@click.argument('url')
@click.option('--topic', '-t', required=False, help='Topic to focus on (can use multiple words)')
@click.option('--depth', '-d', default=1, help='Crawl depth (1 = single page, 2+ = follow links)')
@click.option('--max-pages', '-m', default=3, help='Maximum number of pages to crawl')
@click.option('--no-llm', is_flag=True, help='Use non-LLM extraction method (simpler but faster)')
@click.option("--include-images", is_flag=True, help="Extract and save images from the website")
@click.option("--max-images", type=int, default=10, help="Maximum number of images to extract per page")
@click.option("--min-image-size", type=int, default=100, help="Minimum width/height in pixels for images to extract")
@click.option("--image-dir", type=click.Path(), help="Custom directory to save extracted images")
def scrape(url: str, topic: str = None, depth: int = 1, max_pages: int = 3, no_llm: bool = False,
           include_images: bool = False, max_images: int = 10, min_image_size: int = 100, 
           image_dir: str = None):
    """Scrape structured data from a website.
    
    Examples:
        cliche scrape https://example.com --topic "Machine Learning"
        cliche scrape https://docs.python.org --topic "Python async" --depth 2
        cliche scrape https://developer.mozilla.org --topic "JavaScript" --depth 3 --max-pages 10
        cliche scrape https://example.com --depth 1
        cliche scrape https://docs.python.org --include-images --max-images 20  # Extract images
    """
    success = asyncio.run(async_scrape(url, topic, depth, max_pages, no_llm, 
                                       include_images, max_images, min_image_size, image_dir))
    
    if success and topic:
        click.echo(f"\n💡 Tip: Run 'cliche generate {topic}' to create a document from the scraped data")
    elif success:
        domain = urlparse(url).netloc.split('.')[-2]  # e.g., docs.python.org -> python
        click.echo(f"\n💡 Tip: Run 'cliche generate scraped_{domain}' to create a document from the scraped data")

async def async_scrape(url, topic=None, depth=1, max_pages=3, no_llm=False,
                      include_images=False, max_images=10, min_image_size=100, image_dir=None):
    """Scrape structured data from a site based on a topic with multi-page support."""
    # Set environment variable for LLM usage
    if no_llm:
        os.environ["CLICHE_NO_LLM"] = "1"
        click.echo("🔍 LLM extraction disabled, using BeautifulSoup extraction only")
    else:
        # Clear the environment variable if it exists
        if "CLICHE_NO_LLM" in os.environ:
            del os.environ["CLICHE_NO_LLM"]
        
    click.echo(f"🕸️ Scraping {url}" + (f" for topic: '{topic}'" if topic else ""))
    click.echo(f"⚙️ Settings: depth={depth}, max_pages={max_pages}" + (", no-llm=True" if no_llm else ""))
    
    if include_images:
        click.echo(f"🖼️ Image extraction enabled: max={max_images}, min_size={min_image_size}px")
        if image_dir:
            click.echo(f"📂 Custom image directory: {image_dir}")
        else:
            click.echo(f"📂 Default image directory: ~/cliche/files/images/scraped")
            
    # Create crawler instance
    try:
        print("DEBUG: Creating AsyncWebCrawler instance")
        crawler = AsyncWebCrawler()
    except Exception as e:
        click.echo(f"❌ Error initializing crawler: {str(e)}")
        return False
        
    # Normalize base URL
    if not url.startswith('http'):
        url = 'https://' + url
        
    # Check if it's a Wikipedia article
    if is_wikipedia_url(url):
        click.echo("🔍 Detected Wikipedia URL, using direct extraction")
        result, links = await scrape_page(crawler, url, url, set(), topic, 
                                   include_images, max_images, min_image_size, image_dir)
        if result:
            # We need to wrap the result in a list for consistent handling
            results = [result]
        else:
            return False
    # Check if it's a Python.org URL
    elif is_python_org_url(url):
        click.echo("🐍 Using direct Python.org extraction...")
        result, links = await scrape_page(crawler, url, url, set(), topic, 
                                   include_images, max_images, min_image_size, image_dir)
        if result:
            click.echo(f"✅ Extracted {len(result.get('main_content', ''))} characters of Python.org content")
            # We need to wrap the result in a list for consistent handling
            results = [result]
        else:
            return False
    # For regular websites, crawl to the specified depth
    else:
        try:
            print(f"DEBUG: Starting regular website crawl for {url}")
            print(f"DEBUG: Image extraction is {'enabled' if include_images else 'disabled'}")
            
            results = await crawl_site(url, topic, depth, max_pages, include_images, max_images, min_image_size, image_dir)
            
            if not results:
                click.echo(f"❌ No relevant content found for {topic if topic else url}")
                return False
                
            click.echo(f"✨ Found {len(results)} relevant pages")
        except Exception as e:
            import traceback
            print(f"DEBUG: Error during crawling: {str(e)}")
            print(f"DEBUG: Error details: {traceback.format_exc()}")
            return False
    
    # Track if we had any successful saves
    success = False
    
    # Save each result to a separate JSON file
    saved_files = []
    for idx, data in enumerate(results):
        page_url = data.get('url', url)
        domain = urlparse(page_url).netloc.replace('.', '_')
        
        # Create a timestamp for consistent naming with image directories
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename matching image directory pattern
        if topic:
            base_json_filename = f"scraped_{domain}_{topic}_{timestamp}.json"
        else:
            base_json_filename = f"scraped_{domain}_{timestamp}.json"
            
        if len(results) > 1:
            base_json_filename = f"scraped_{domain}_{idx+1}_{timestamp}.json"
        
        # Create file path
        output_dir = Path(os.path.expanduser("~/cliche/files/scrape"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / base_json_filename
        
        # Save the filename without the extension for image folder naming
        base_filename = os.path.splitext(base_json_filename)[0]
        
        with open(output_path, "w") as f:
            # Check if data is a Pydantic model or a dict
            if hasattr(data, 'dict') and callable(getattr(data, 'dict')):
                # It's a Pydantic model
                json.dump(data.dict(), f, indent=2)
            else:
                # It's already a dict
                json.dump(data, f, indent=2)
            
        click.echo(f"✅ Saved content to {output_path}")
        saved_files.append(str(output_path))
        
        # Show image extraction stats
        if isinstance(data, dict) and 'images' in data and data['images']:
            click.echo(f"🖼️ Extracted {len(data['images'])} images from {page_url}")
            # Add info about where images are stored
            if data['images'][0].get('local_path'):
                # Get the directory of the first image
                image_folder = os.path.dirname(data['images'][0]['local_path'])
                click.echo(f"📂 Images saved to {image_folder}")
        elif hasattr(data, 'images') and data.images:
            click.echo(f"🖼️ Extracted {len(data.images)} images from {page_url}")
            # Add info about where images are stored
            if hasattr(data.images[0], 'local_path') and data.images[0].local_path:
                # Get the directory of the first image
                image_folder = os.path.dirname(str(data.images[0].local_path))
                click.echo(f"📂 Images saved to {image_folder}")
                
        print(f"DEBUG: Successfully saved scraped data with {len(data.get('main_content', ''))} chars to {output_path}")
        success = True
    
    # Final output summary to make it clear where files are saved
    if saved_files:
        click.echo("\n📄 Summary of saved files:")
        for file_path in saved_files:
            click.echo(f"  - {file_path}")
    
    return success

# --- Helper functions for improved fallback extraction ---
def process_code_block(element, content_text):
    """Process a code block element with language detection."""
    code_text = element.get_text()
    
    # Detect language if possible
    language = "text"  # Default language
    if 'class' in element.attrs:
        classes = element['class']
        for cls in classes:
            if isinstance(cls, str):
                if cls.startswith('language-'):
                    language = cls.replace('language-', '')
                elif cls in ['python', 'javascript', 'java', 'cpp', 'csharp', 'html', 'css', 'bash', 'sql']:
                    language = cls
    
    # Check parent for language classes
    if element.parent and 'class' in element.parent.attrs:
        classes = element.parent['class']
        for cls in classes:
            if isinstance(cls, str):
                if cls.startswith('language-'):
                    language = cls.replace('language-', '')
    
    # Try to detect language by content patterns
    if language == "text":
        if 'def ' in code_text or 'import ' in code_text or 'class ' in code_text:
            language = "python"
        elif 'function ' in code_text or 'var ' in code_text or 'const ' in code_text:
            language = "javascript"
        elif '<html' in code_text or '<div' in code_text:
            language = "html"
        elif '{' in code_text and '}' in code_text and ';' in code_text:
            language = "java"  # Could be Java, C#, etc.
    
    # Format the code block with proper fences and language
    content_text += f"```{language}\n{code_text}\n```\n\n"
    
def extract_table_as_markdown(table):
    """Convert an HTML table to markdown format."""
    md_table = ""
    
    # Process table headers
    headers = table.find_all('th')
    if headers:
        md_table += "| "
        for header in headers:
            md_table += f"{header.get_text(strip=True)} | "
        md_table += "\n| "
        md_table += " --- |" * len(headers)
        md_table += "\n"
    
    # Process table rows
    for row in table.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        if cells and not (len(cells) == 1 and cells[0].find('th')):  # Skip header row we already processed
            row_content = "| "
            for cell in cells:
                row_content += f"{cell.get_text(strip=True)} | "
            md_table += row_content + "\n"
    
    return md_table

def process_div_content(div):
    """Recursively process content within divs."""
    content = ""
    
    # Process headings
    for h_tag in div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False):
        level = int(h_tag.name[1])
        heading_text = h_tag.get_text(strip=True)
        content += f"{'#' * level} {heading_text}\n\n"
    
    # Process paragraphs
    for p in div.find_all('p', recursive=False):
        text = p.get_text(strip=True)
        if text:
            content += f"{text}\n\n"
    
    # Process lists
    for list_elem in div.find_all(['ul', 'ol'], recursive=False):
        for li in list_elem.find_all('li'):
            content += f"* {li.get_text(strip=True)}\n"
        content += "\n"
    
    # Process code blocks
    for code in div.find_all(['pre', 'code'], recursive=False):
        code_text = code.get_text()
        content += f"```\n{code_text}\n```\n\n"
    
    # Process tables
    for table in div.find_all('table', recursive=False):
        content += extract_table_as_markdown(table) + "\n\n"
    
    return content
