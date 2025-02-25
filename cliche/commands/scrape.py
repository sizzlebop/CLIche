import os
import json
import asyncio
import click
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field
from ..core import CLIche
from bs4 import BeautifulSoup
from pathlib import Path

# --- Structured Data Schema ---
class ScrapedData(BaseModel):
    title: str = Field(..., description="Title of the page.")
    description: str = Field(..., description="A detailed summary of the page content.")
    main_content: str = Field(..., description="Complete and comprehensive content of the page.")

# --- Helper Functions ---
def is_same_domain(url1: str, url2: str) -> bool:
    return urlparse(url1).netloc == urlparse(url2).netloc

def is_relevant_content(text: str, topic: str) -> bool:
    """Check if extracted text is relevant to the topic with improved relevance scoring."""
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

def is_url_relevant(url: str, topic: str) -> bool:
    """Check if URL seems relevant to the topic based on its text."""
    # Extract words from URL path
    path_words = urlparse(url).path.lower().replace('-', ' ').replace('_', ' ').replace('/', ' ').split()
    
    # Check for topic words in URL path
    topic_words = set(topic.lower().split())
    matches = sum(1 for word in path_words if any(topic_word in word for topic_word in topic_words))
    
    return matches > 0

# --- Scraping Logic ---
async def scrape_page(crawler, url, base_url, visited, topic):
    """Scrape a page and return structured data if relevant."""
    try:
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
                cliche = CLIche()
                provider_name = cliche.config.config.get("active_provider")
                if not provider_name:
                    raise ValueError("No active provider configured")
                    
                provider_config = cliche.config.get_provider_config(provider_name)
                if not provider_config:
                    raise ValueError(f"No configuration found for provider '{provider_name}'")
                    
                model = provider_config.get("model")
                if not model:
                    raise ValueError(f"No model specified for provider '{provider_name}'")
                    
                # Clean up the content
                for tag in main_content.find_all(['a', 'img']):
                    # Convert relative URLs to absolute
                    if 'href' in tag.attrs:
                        tag['href'] = urljoin(url, tag['href'])
                    if 'src' in tag.attrs:
                        tag['src'] = urljoin(url, tag['src'])
                        
                # Create extraction strategy for the cleaned content with enhanced prompt
                extraction_strategy = LLMExtractionStrategy(
                    provider=f"{provider_name}/{model}",  # Format: provider/model
                    schema=ScrapedData.schema(),
                    extraction_type="schema",
                    instruction=f"""Extract COMPLETE and COMPREHENSIVE structured data about '{topic}' from this page.
                    
                    The response should be in JSON format with these fields:
                    - title: {title if title else 'The main title of the article'}
                    - description: A detailed summary (100-200 words) of what the article covers
                    - main_content: The FULL article content with ALL technical details, formatted as markdown.
                    
                    CRITICAL EXTRACTION REQUIREMENTS:
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
                    
                    This extraction will be used for technical documentation, so completeness and accuracy are critical."""
                )
                
                # Extract structured data using LLM
                extracted_data = extraction_strategy.extract(url=url, ix=0, html=str(main_content))
                
                if not extracted_data:
                    raise ValueError("No structured data could be extracted using LLM")
                    
                # Get the first block since we're using schema extraction
                if isinstance(extracted_data, list) and extracted_data:
                    extracted_data = extracted_data[0]
                    
                if not is_relevant_content(extracted_data.get("main_content", ""), topic):
                    return None, result.links or []
                    
                return extracted_data, result.links or []
                
            except Exception as e:
                click.echo(f"ℹ️ LLM extraction failed: {str(e)}. Falling back to non-LLM extraction.")
                use_fallback = True
                
        # If we get here, use the fallback extraction
        if use_fallback:
            # Convert HTML to markdown-like content
            content_text = ""
            
            # Extract headings
            for h_tag in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_level = int(h_tag.name[1])
                heading_text = h_tag.get_text(strip=True)
                content_text += f"{'#' * heading_level} {heading_text}\n\n"
                
                # Get content until next heading
                sibling = h_tag.find_next_sibling()
                while sibling and sibling.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if sibling.name == 'p':
                        content_text += f"{sibling.get_text(strip=True)}\n\n"
                    elif sibling.name == 'ul' or sibling.name == 'ol':
                        for li in sibling.find_all('li', recursive=False):
                            content_text += f"* {li.get_text(strip=True)}\n"
                        content_text += "\n"
                    elif sibling.name == 'pre' or sibling.name == 'code':
                        content_text += f"```\n{sibling.get_text()}\n```\n\n"
                    elif sibling.name == 'table':
                        content_text += "Table content (simplified in fallback mode)\n\n"
                    sibling = sibling.find_next_sibling()
            
            # If no headings, just extract all paragraphs
            if not content_text:
                for p in main_content.find_all('p'):
                    content_text += f"{p.get_text(strip=True)}\n\n"
            
            # Create a basic description
            description = ""
            for p in main_content.find_all('p')[:3]:  # First 3 paragraphs
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
            
            return fallback_data, result.links or []
            
    except Exception as e:
        click.echo(f"⚠️ Error during scraping: {str(e)}")
        return None, []

async def crawl_site(url, topic, max_depth=2, max_pages=5):
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

async def async_scrape(url, topic, depth=1, max_pages=3, no_llm=False):
    """Scrape structured data from a site based on a topic with multi-page support."""
    click.echo(f"🔍 Scraping content about '{topic}' from {url}" + 
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
        click.echo(f"❌ No relevant content found for '{topic}' at {url}")
        return False
    
    # Save to JSON file
    json_filename = topic.replace(' ', '_').lower() + '.json'
    output_dir = Path(os.path.expanduser("~/.cliche/files/scrape"))
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / json_filename
    
    # Load existing data if file exists
    existing_data = []
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
    
    # Save updated data
    if new_items_count > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        click.echo(f"✅ Saved {new_items_count} new content items to {json_path}")
    else:
        click.echo(f"ℹ️ No new content to save (already exists in {json_path})")
    
    return new_items_count > 0

@click.command()
@click.argument('url')
@click.option('--topic', '-t', required=True, help='Topic to focus on (can use multiple words)')
@click.option('--depth', '-d', default=1, help='Crawl depth (1 = single page, 2+ = follow links)')
@click.option('--max-pages', '-m', default=3, help='Maximum number of pages to crawl')
@click.option('--no-llm', is_flag=True, help='Use non-LLM extraction method (simpler but faster)')
def scrape(url: str, topic: str, depth: int, max_pages: int, no_llm: bool = False):
    """Scrape structured data from a website.
    
    Examples:
        cliche scrape https://example.com --topic "Machine Learning"
        cliche scrape https://docs.python.org --topic "Python async" --depth 2
        cliche scrape https://developer.mozilla.org --topic "JavaScript" --depth 3 --max-pages 10
    """
    success = asyncio.run(async_scrape(url, topic, depth, max_pages, no_llm))
    if success:
        click.echo(f"\n💡 Tip: Run 'cliche generate {topic}' to create a document from the scraped data")
