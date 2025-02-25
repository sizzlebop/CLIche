import os
import json
import asyncio
import click
from pathlib import Path
from duckduckgo_search import DDGS  # Web search tool
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from .write import async_write

def perform_search(query, num_results=5):
    """Perform a DuckDuckGo search and return the top results."""
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

SCRAPE_OUTPUT_DIR = os.path.expanduser("~/.cliche/files/research")

@click.command()
@click.argument("query", nargs=-1)
@click.option("--depth", "-d", type=int, default=3, help="Number of search results to analyze")
@click.option("--format", "-f", type=click.Choice(["text", "markdown", "html"]), default="markdown", help="Output format")
def research(query, depth, format):
    """Perform a real-time research query and generate a well-structured summary."""
    
    query = " ".join(query)  # Convert tuple of words into a single string
    
    click.echo(f"🔍 Researching: {query}...")

    # Perform a web search
    search_results = perform_search(query, num_results=depth)

    if not search_results:
        click.echo("❌ No search results found.")
        return
    
    # Select top N results
    selected_results = search_results[:depth]
    
    extracted_data = []
    
    async def scrape_and_extract():
        async with AsyncWebCrawler() as crawler:
            for result in selected_results:
                url = result['link']
                title = result['title']
                
                if not url:
                    continue
                
                click.echo(f"🌐 Scraping: {url}")
                
                try:
                    config = CrawlerRunConfig(
                        page_timeout=30000,
                        wait_until='load',
                        scan_full_page=True,
                        word_count_threshold=100
                    )
                    content = await crawler.extract_content(url, config)
                    
                    if content and content.cleaned_html:
                        extracted_data.append({
                            "title": title,
                            "url": url,
                            "content": content.cleaned_html,
                            "snippet": result.get('snippet', '')
                        })
                        click.echo(f"✅ Extracted content from: {title}")
                    else:
                        click.echo(f"⚠️  No content extracted from: {title}")
                except Exception as e:
                    click.echo(f"❌ Error scraping {url}: {str(e)}")
    
    # Run the scraping
    asyncio.run(scrape_and_extract())
    
    if not extracted_data:
        click.echo("❌ No content could be extracted from any sources.")
        return
    
    # Format the research prompt for the LLM
    prompt = f"Generate a well-structured research report on '{query}' using the following sources:\n\n"

    for item in extracted_data:
        prompt += f"# {item['title']}\n\n"
        prompt += f"**Source:** {item['url']}\n\n"
        prompt += f"## Extracted Content\n{item['content'][:2000]}...\n\n"  # Trimmed to avoid overload
        prompt += f"## Summary\n{item['snippet']}\n\n"
        prompt += "---\n\n"

    # Save raw data
    os.makedirs(SCRAPE_OUTPUT_DIR, exist_ok=True)
    json_path = Path(SCRAPE_OUTPUT_DIR) / f"{query.replace(' ', '_')}.json"
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4)
    
    click.echo(f"📄 Extracted data saved: {json_path}")
    
    # Pass data to the LLM for a proper structured summary
    asyncio.run(async_write((prompt,), format, None))

if __name__ == "__main__":
    research()
