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
from ..utils.file import get_unique_filename
import re

# --- Structured Data Schema ---
class ScrapedData(BaseModel):
    title: str = Field(..., description="Title of the page.")
    description: str = Field(..., description="A detailed summary of the page content.")
    main_content: str = Field(..., description="Complete and comprehensive content of the page.")

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

# --- Scraping Logic ---
async def scrape_page(crawler, url, base_url, visited, topic=None):
    """Scrape a page and return structured data if relevant."""
    try:
        # Special handling for Wikipedia - use direct requests instead of crawler
        if is_wikipedia_url(url):
            click.echo("📝 Using direct Wikipedia extraction...")
            return await extract_wikipedia_directly(url, topic)
            
        config = CrawlerRunConfig(
            page_timeout=60000,
            wait_until='load',
            scan_full_page=True,
            magic=False,
            word_count_threshold=100,  # Increased threshold for more substantive pages
        )
        
        # First get the raw content
        result = await crawler.arun(url=url, config=config)
        if not result or not result.cleaned_html:
            click.echo(f"⚠️ Failed to fetch content from {url}")
            return None, []
            
        # Extract main content using BeautifulSoup
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
            click.echo(f"⚠️ Could not find main content in {url}")
            return None, []
            
        # Get the title
        title = soup.title.string if soup.title else ""
        if not title:
            for selector in ['h1.article-title', 'h1.title', 'h1']:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
        
        # Check if we should use non-LLM extraction
        if os.environ.get("CLICHE_NO_LLM") == "1":
            use_fallback = True
        else:
            use_fallback = False
            
        # Try to use LLM extraction if provider is configured and not in fallback mode
        if not use_fallback:
            try:
                # Try to get the LLM using the helper function that works in other commands
                llm = get_llm()
                if not llm:
                    raise ValueError("No LLM provider configured")
                
                # Print debug information about the LLM
                provider_name = "unknown"
                model = "unknown"
                
                # Try various possible attribute names for provider and model
                if hasattr(llm, 'provider_name'):
                    provider_name = llm.provider_name
                elif hasattr(llm, 'name'):
                    provider_name = llm.name
                elif hasattr(llm, 'provider'):
                    provider_name = llm.provider
                
                if hasattr(llm, 'model'):
                    model = llm.model
                elif hasattr(llm, 'model_name'):
                    model = llm.model_name
                elif hasattr(llm, 'active_model'):
                    model = llm.active_model
                
                click.echo(f"📝 Using LLM extraction with provider: {provider_name}, model: {model}")
                    
                # Clean up the content
                for tag in main_content.find_all(['a', 'img']):
                    # Convert relative URLs to absolute
                    if 'href' in tag.attrs:
                        tag['href'] = urljoin(url, tag['href'])
                    if 'src' in tag.attrs:
                        tag['src'] = urljoin(url, tag['src'])
                
                # Prepare a prompt for direct LLM usage
                topic_str = f"about '{topic}'" if topic else "from this web page"
                prompt = f"""<SYSTEM>
You are a data extraction system that ONLY outputs valid JSON. You never add explanatory text. You only output correctly formatted JSON data structures.
</SYSTEM>

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
- "main_content": The FULL article content with ALL technical details, formatted as markdown.

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
                
                # Create a function to run the LLM in a separate thread to avoid event loop issues
                def run_llm_in_thread():
                    import threading
                    result = {"success": False, "data": None, "error": None}
                    
                    def thread_func():
                        try:
                            # Create a new event loop for this thread
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            # Run the coroutine in this thread's event loop
                            response = loop.run_until_complete(llm.generate_response(prompt, professional_mode=True))
                            result["success"] = True
                            result["data"] = response
                        except Exception as e:
                            result["error"] = str(e)
                        finally:
                            loop.close()
                    
                    # Start the thread and wait for it to complete
                    thread = threading.Thread(target=thread_func)
                    thread.start()
                    thread.join()
                    
                    return result
                
                # Run the LLM in a separate thread
                llm_result = run_llm_in_thread()
                
                if not llm_result["success"]:
                    error_msg = llm_result.get("error", "Unknown error")
                    click.echo(f"⚠️ Error executing LLM in thread: {error_msg}")
                    raise ValueError(f"Failed to execute LLM: {error_msg}")
                
                extracted_json = llm_result["data"]
                
                # Parse the JSON response
                try:
                    import json
                    
                    # Clean up the response before parsing
                    extracted_text = extracted_json.strip()
                    
                    # Look for common conversational prefixes to remove
                    conversational_prefixes = [
                        "Here's the JSON:",
                        "Here's the extracted data:",
                        "Certainly!",
                        "Sure!",
                        "Here's the information",
                        "Here is the"
                    ]
                    
                    for prefix in conversational_prefixes:
                        if extracted_text.startswith(prefix):
                            # Remove the prefix and any whitespace/newlines after it
                            prefix_end = len(prefix)
                            extracted_text = extracted_text[prefix_end:].strip()
                    
                    # Try to find a JSON object within the text
                    json_patterns = [
                        r'```json\s*([\s\S]*?)\s*```',  # JSON in code fence
                        r'```\s*([\s\S]*?)\s*```',      # Any code fence
                        r'({[\s\S]*})',                 # Any JSON-like structure with braces
                    ]
                    
                    parsed = False
                    for pattern in json_patterns:
                        if parsed:
                            break
                            
                        matches = re.search(pattern, extracted_text)
                        if matches:
                            potential_json = matches.group(1).strip()
                            try:
                                extracted_data = json.loads(potential_json)
                                click.echo("✅ Successfully extracted JSON using pattern matching")
                                parsed = True
                            except json.JSONDecodeError:
                                # Try to fix common JSON issues
                                try:
                                    # Remove trailing commas
                                    fixed_json = re.sub(r',\s*}', '}', potential_json)
                                    fixed_json = re.sub(r',\s*]', ']', fixed_json)
                                    extracted_data = json.loads(fixed_json)
                                    click.echo("✅ Successfully extracted JSON after fixing format issues")
                                    parsed = True
                                except json.JSONDecodeError:
                                    # Keep trying with next pattern
                                    continue

                    # If pattern matching didn't work, try direct parsing
                    if not parsed:
                        try:
                            # Try direct JSON parsing as a last resort
                            extracted_data = json.loads(extracted_text)
                            click.echo("✅ Successfully parsed raw text as JSON")
                            parsed = True
                        except json.JSONDecodeError:
                            # Find first { and last } as a last resort
                            first_brace = extracted_text.find('{')
                            last_brace = extracted_text.rfind('}')
                            
                            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                                potential_json = extracted_text[first_brace:last_brace+1]
                                try:
                                    # Fix common issues and try again
                                    potential_json = re.sub(r',\s*}', '}', potential_json)
                                    potential_json = re.sub(r',\s*]', ']', potential_json)
                                    extracted_data = json.loads(potential_json)
                                    click.echo("✅ Successfully extracted JSON by finding braces")
                                    parsed = True
                                except json.JSONDecodeError:
                                    # Final failure
                                    raise ValueError("Could not parse any valid JSON from the LLM response")
                    
                    if not extracted_data:
                        click.echo(f"⚠️ LLM extraction returned no data, falling back to standard extraction")
                        raise ValueError("No structured data could be extracted using LLM")
                    
                    click.echo(f"✅ Successfully extracted content using LLM")
                    
                    # Make sure main_content is set
                    if "main_content" not in extracted_data:
                        extracted_data["main_content"] = ""
                    
                    if not is_relevant_content(extracted_data.get("main_content", ""), topic):
                        return None, result.links or []
                        
                    return extracted_data, result.links or []
                    
                except json.JSONDecodeError as e:
                    click.echo(f"⚠️ Failed to parse LLM output as JSON: {str(e)}")
                    # Print a portion of the output for debugging
                    max_output_length = min(len(extracted_json), 200)
                    click.echo(f"First {max_output_length} characters of output: {extracted_json[:max_output_length]}")
                    
                    # Attempt to extract a JSON object if the LLM included explanatory text
                    json_pattern = r'({[\s\S]*})'
                    json_match = re.search(json_pattern, extracted_json)
                    if json_match:
                        potential_json = json_match.group(1)
                        try:
                            extracted_data = json.loads(potential_json)
                            click.echo("✅ Successfully extracted JSON from LLM response!")
                        except json.JSONDecodeError:
                            # Still couldn't parse as JSON, fall back
                            raise ValueError(f"Invalid JSON format from LLM: {str(e)}")
                    else:
                        # No JSON-like structure found, raise error
                        raise ValueError(f"Invalid JSON format from LLM: {str(e)}")
                
            except Exception as e:
                error_msg = f"ℹ️ LLM extraction failed: {str(e)}. Falling back to non-LLM extraction."
                click.echo(error_msg)
                use_fallback = True
                
        # If we get here, use the fallback extraction
        if use_fallback:
            click.echo("📄 Using non-LLM extraction method for comprehensive content extraction")
            
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
                    
                    # Add the heading
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
            
            click.echo(f"✅ Extracted {len(content_text)} characters of content with non-LLM method")
            return fallback_data, result.links or []
            
    except Exception as e:
        click.echo(f"⚠️ Error during scraping: {str(e)}")
        return None, []

async def extract_wikipedia_directly(url, topic=None):
    """Extract content from Wikipedia pages using direct requests."""
    try:
        # Use a proper user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml'
        }
        
        click.echo(f"🌐 Directly fetching Wikipedia page: {url}")
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
            click.echo(f"📝 Found description: {description[:100]}...")
        
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
                            li_text = li.get_text(strip=True)
                            if li_text:
                                main_content += f"* {li_text}\n"
                        main_content += "\n"
            
            # Extract links for further crawling
            for a in element.find_all('a', href=True):
                href = a.get('href', '')
                if href.startswith('/wiki/') and ':' not in href:  # Skip special pages
                    full_url = 'https://en.wikipedia.org' + href
                    link_targets.append(full_url)
        
        # Check if content is relevant to topic
        if not is_relevant_content(main_content, topic):
            click.echo(f"⚠️ Wikipedia content not relevant to topic '{topic}'")
            return None, link_targets
        
        # Create data structure
        wiki_data = {
            "title": title,
            "description": description[:500] + "..." if len(description) > 500 else description,
            "main_content": main_content,
            "url": url
        }
        
        click.echo(f"✅ Extracted {len(main_content)} characters of Wikipedia content")
        return wiki_data, link_targets
        
    except Exception as e:
        click.echo(f"❌ Error in direct Wikipedia extraction: {str(e)}")
        import traceback
        click.echo(f"  Error details: {traceback.format_exc()}")
        return None, []

async def crawl_site(url, topic=None, max_depth=2, max_pages=5):
    """Crawl a site to a certain depth, focusing on relevant content."""
    visited = set()
    to_visit = [(url, 0)]  # (URL, depth)
    results = []
    
    async with AsyncWebCrawler() as crawler:
        while to_visit and len(results) < max_pages:
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited or depth > max_depth:
                continue
                
            visited.add(current_url)
            click.echo(f"🕸️ Crawling ({depth}/{max_depth}): {current_url}")
            
            data, links = await scrape_page(crawler, current_url, url, visited, topic)
            if data:
                # Add URL to the data
                data['url'] = current_url
                results.append(data)
                click.echo(f"✨ Found relevant content: {data.get('title', 'Untitled')}")
                
            # Only follow links from same domain that appear relevant
            if depth < max_depth:
                for link in links:
                    if link not in visited and is_same_domain(url, link):
                        # Check link relevance based on URL text
                        if is_url_relevant(link, topic):
                            to_visit.append((link, depth + 1))
                            
    return results

async def async_scrape(url, topic=None, depth=1, max_pages=3, no_llm=False):
    """Scrape structured data from a site based on a topic with multi-page support."""
    topic_msg = f" about '{topic}'" if topic else ""
    click.echo(f"🔍 Scraping content{topic_msg} from {url}" + 
             (f" (crawling to depth {depth}, max {max_pages} pages)" if depth > 1 or max_pages > 1 else "") +
             (f" [No LLM mode]" if no_llm else ""))
    
    # Set flag in global scope to use fallback extraction
    if no_llm:
        click.echo("ℹ️ Using non-LLM extraction method (--no-llm flag enabled)")
        os.environ["CLICHE_NO_LLM"] = "1"
    else:
        os.environ.pop("CLICHE_NO_LLM", None)
    
    if depth > 1 or max_pages > 1:
        # Use multi-page crawling
        results = await crawl_site(url, topic, max_depth=depth, max_pages=max_pages)
    else:
        # Use single-page scraping (original behavior)
        async with AsyncWebCrawler() as crawler:
            data, _ = await scrape_page(crawler, url, url, set(), topic)
            results = [data] if data else []
    
    if not results:
        topic_msg = f" for '{topic}'" if topic else ""
        click.echo(f"❌ No relevant content found{topic_msg} at {url}")
        return False
    
    # Save to JSON file
    # Use the domain name as the filename if no topic is provided
    if topic:
        base_json_filename = topic.replace(' ', '_').lower() + '.json'
    else:
        domain = urlparse(url).netloc.replace('.', '_')
        base_json_filename = f"scraped_{domain}.json"
        
    output_dir = Path(os.path.expanduser("~/cliche/files/scrape"))
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / base_json_filename
    
    # Load existing data if file exists
    existing_data = []
    new_file_needed = False
    
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            pass
    
    # Process each result
    new_items_count = 0
    for data in results:
        if data:
            # Check if URL already exists
            result_url = data.get('url', url)
            if not any(entry.get('url') == result_url for entry in existing_data):
                # Append new data only if URL doesn't exist
                existing_data.append(data)
                new_items_count += 1
    
    # Check if we should create a new file instead
    if new_items_count == 0 and json_path.exists():
        # Get a unique filename since we have no new data for existing file
        json_filename = get_unique_filename(output_dir, base_json_filename)
        json_path = output_dir / json_filename
        new_file_needed = True
        
        # Start a new file with just our current results
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        click.echo(f"✅ Created new file with current data at {json_path}")
    else:
        # We either have new content to add to existing file or creating a new file
        if new_items_count > 0 or not json_path.exists():
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            click.echo(f"✅ Saved {new_items_count} new content items to {json_path}")
        else:
            click.echo(f"ℹ️ No new content to save (already exists in {json_path})")
            suggestion = len(existing_data) + 1 if existing_data else 1
            click.echo(f"ℹ️ Tip: Use 'cliche scrape {url} --topic \"{topic}_{suggestion}\"' to create a new file")
    
    return new_items_count > 0 or new_file_needed

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

@click.command()
@click.argument('url')
@click.option('--topic', '-t', required=False, help='Topic to focus on (can use multiple words)')
@click.option('--depth', '-d', default=1, help='Crawl depth (1 = single page, 2+ = follow links)')
@click.option('--max-pages', '-m', default=3, help='Maximum number of pages to crawl')
@click.option('--no-llm', is_flag=True, help='Use non-LLM extraction method (simpler but faster)')
def scrape(url: str, topic: str = None, depth: int = 1, max_pages: int = 3, no_llm: bool = False):
    """Scrape structured data from a website.
    
    Examples:
        cliche scrape https://example.com --topic "Machine Learning"
        cliche scrape https://docs.python.org --topic "Python async" --depth 2
        cliche scrape https://developer.mozilla.org --topic "JavaScript" --depth 3 --max-pages 10
        cliche scrape https://example.com --depth 1
    """
    success = asyncio.run(async_scrape(url, topic, depth, max_pages, no_llm))
    if success:
        if topic:
            click.echo(f"\n💡 Tip: Run 'cliche generate {topic}' to create a document from the scraped data")
        else:
            domain = urlparse(url).netloc.replace('.', '_')
            click.echo(f"\n💡 Tip: Run 'cliche generate scraped_{domain}' to create a document from the scraped data")
