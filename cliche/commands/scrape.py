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
    description: str = Field(..., description="A brief summary of the page.")
    main_content: str = Field(..., description="Main body of the article or page.")

# --- Helper Functions ---
def is_same_domain(url1: str, url2: str) -> bool:
    return urlparse(url1).netloc == urlparse(url2).netloc

def is_relevant_content(text: str, topic: str) -> bool:
    """Check if extracted text is relevant to the topic."""
    topic_words = set(topic.lower().split())
    return any(word in text.lower() for word in topic_words)

# --- Scraping Logic ---
async def scrape_page(crawler, url, base_url, visited, topic):
    """Scrape a page and return structured data if relevant."""
    try:
        config = CrawlerRunConfig(
            page_timeout=60000,
            wait_until='load',
            scan_full_page=True,
            magic=False,
            word_count_threshold=50,  # Ignore tiny pages
        )
        
        # Get the current CLIche configuration
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
        except Exception as e:
            raise click.UsageError(f"Configuration error: {str(e)}")
            
        try:
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
            for selector in ['main article', 'main', 'article', '.main-content', '#content', '.content', '[role="main"]']:
                main_content = soup.select_one(selector)
                if main_content and len(str(main_content)) > 500:  # Must be substantial content
                    break
                    
            # If no main content found, try to get the largest content block
            if not main_content:
                content_blocks = []
                for tag in soup.find_all(['div', 'section']):
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
                        
            # Clean up the content
            for tag in main_content.find_all(['a', 'img']):
                # Convert relative URLs to absolute
                if 'href' in tag.attrs:
                    tag['href'] = urljoin(url, tag['href'])
                if 'src' in tag.attrs:
                    tag['src'] = urljoin(url, tag['src'])
                    
            # Create extraction strategy for the cleaned content
            extraction_strategy = LLMExtractionStrategy(
                provider=f"{provider_name}/{model}",  # Format: provider/model
                schema=ScrapedData.schema(),
                extraction_type="schema",
                instruction=f"""Extract structured data about '{topic}' from this page.
                The response should be in JSON format with these fields:
                - title: {title if title else 'The main title of the article'}
                - description: A brief summary of what the article is about
                - main_content: The actual article content, formatted as markdown.
                
                Important:
                1. Include ALL relevant code examples and technical details
                2. Keep the original structure with headings and sections
                3. Preserve code blocks and their syntax
                4. Include key concepts and explanations
                5. Make sure to capture the full depth of the technical content"""
            )
            
            # Extract structured data using LLM
            extracted_data = extraction_strategy.extract(url=url, ix=0, html=str(main_content))
            if not extracted_data:
                click.echo(f"⚠️ No structured data could be extracted from {url}")
                return None, []
                
            # Get the first block since we're using schema extraction
            if isinstance(extracted_data, list) and extracted_data:
                extracted_data = extracted_data[0]
                
            if not is_relevant_content(extracted_data.get("main_content", ""), topic):
                return None, []
                
            return extracted_data, result.links or []
        except Exception as e:
            click.echo(f"⚠️ Error during scraping: {str(e)}")
            return None, []
    except Exception as e:
        click.echo(f"⚠️ Error during scraping: {str(e)}")
        return None, []

async def async_scrape(url, topic):
    """Scrape structured data from a site based on a topic."""
    async with AsyncWebCrawler() as crawler:
        data, links = await scrape_page(crawler, url, url, set(), topic)
        if data:
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
            
            # Add URL to data
            data['url'] = url
            
            # Check if URL already exists
            if not any(entry.get('url') == url for entry in existing_data):
                # Append new data only if URL doesn't exist
                existing_data.append(data)
                
                # Save updated data
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)
                
                click.echo(f"✅ Saved scraped data to {json_path}")
            else:
                click.echo(f"ℹ️ Content from {url} already exists in {json_path}")
            return True
        return False

@click.command()
@click.argument('url')
@click.option('--topic', '-t', required=True, help='Topic to focus on')
def scrape(url: str, topic: str):
    """Scrape structured data from a website.
    
    Examples:
        cliche scrape https://example.com --topic "Machine Learning"
        cliche scrape https://docs.python.org --topic "Python async"
    """
    success = asyncio.run(async_scrape(url, topic))
    if success:
        click.echo(f"\n💡 Tip: Run 'cliche generate {topic}' to create a document from the scraped data")
