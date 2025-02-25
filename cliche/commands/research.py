import os
import json
import asyncio
import click
import re
import inspect
from pathlib import Path
from ..core import cli, CLIche, get_llm
from ..utils.file import save_text_to_file, get_output_dir

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
def research(query, depth, debug, fallback_only, write, format, filename):
    """Research a topic by searching the web and generating a response based on findings.
    
    Examples:
        cliche research current AI developments
        cliche research "Python best practices 2023" --depth 5
        cliche research "Climate change solutions" --write --format markdown
        cliche research "Quantum computing advances" --write --filename quantum_research.md
    """
    
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
        
    query_str = " ".join(query)  # Convert tuple of words into a single string
    
    if not query_str:
        click.echo("Error: No query provided. Please specify what you want to research.")
        return
    
    click.echo(f"🔍 Researching: {query_str}...")

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
                        
                        click.echo(f"🌐 Scraping: {title}")
                        
                        try:
                            if debug:
                                click.echo(f"  Creating crawler config for {url}")
                            
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
                                click.echo(f"✅ Content extracted: {len(extracted_text)} chars")
                            else:
                                # Try fallback scraping
                                click.echo(f"⚠️ Primary extraction failed for {title}, trying fallback method...")
                                fallback_content = await fallback_scrape(url, debug)
                                
                                if fallback_content and len(fallback_content) > 100:
                                    extracted_text = fallback_content[:3000]  # Limit content size
                                    extracted_data.append({
                                        "title": title,
                                        "url": url,
                                        "content": extracted_text,
                                        "snippet": result.get('snippet', '')
                                    })
                                    click.echo(f"✅ Fallback extraction succeeded: {len(extracted_text)} chars")
                                else:
                                    click.echo(f"⚠️ No content extracted from: {title}")
                        except Exception as e:
                            error_msg = f"❌ Error scraping {url}: {str(e)}"
                            if debug:
                                import traceback
                                error_msg += f"\n{traceback.format_exc()}"
                            click.echo(error_msg)
                            
                            # Always try fallback when crawler fails
                            try:
                                click.echo(f"⚠️ Trying fallback scraper after error...")
                                fallback_content = await fallback_scrape(url, debug)
                                
                                if fallback_content and len(fallback_content) > 100:
                                    extracted_text = fallback_content[:3000]  # Limit content size
                                    extracted_data.append({
                                        "title": title,
                                        "url": url,
                                        "content": extracted_text,
                                        "snippet": result.get('snippet', '')
                                    })
                                    click.echo(f"✅ Fallback extraction succeeded: {len(extracted_text)} chars")
                            except Exception as inner_e:
                                if debug:
                                    click.echo(f"⚠️ Fallback scraper also failed: {str(inner_e)}")
            except Exception as e:
                error_msg = f"❌ Error initializing crawler: {str(e)}"
                if debug:
                    import traceback
                    error_msg += f"\n{traceback.format_exc()}"
                click.echo(error_msg)
                click.echo("⚠️ Falling back to simple scraper for all URLs")
        
        # If fallback-only mode or crawler failed completely, use fallback on all URLs
        if fallback_only or (not use_crawler) or (use_crawler and not extracted_data):
            for result in selected_results:
                url = result['link']
                title = result['title']
                
                if not url:
                    continue
                
                if not fallback_only:  # Only show this message if we're not intentionally using fallback only
                    click.echo(f"🌐 Fallback scraping: {title}")
                else:
                    click.echo(f"🌐 Scraping: {title}")
                    
                try:
                    fallback_content = await fallback_scrape(url, debug)
                    
                    if fallback_content and len(fallback_content) > 100:
                        extracted_text = fallback_content[:3000]  # Limit content size
                        extracted_data.append({
                            "title": title,
                            "url": url,
                            "content": extracted_text,
                            "snippet": result.get('snippet', '')
                        })
                        click.echo(f"✅ Content extracted: {len(extracted_text)} chars")
                    else:
                        click.echo(f"⚠️ No content extracted from: {title}")
                except Exception as e:
                    error_msg = f"❌ Error scraping {url}: {str(e)}"
                    if debug:
                        import traceback
                        error_msg += f"\n{traceback.format_exc()}"
                    click.echo(error_msg)
    
    # Run the scraping
    asyncio.run(scrape_and_extract())
    
    if not extracted_data:
        click.echo("❌ No content could be extracted from any sources.")
        return 1  # Return error code for better detection in test script
    
    # Format the research prompt for the LLM
    prompt = f"""Research query: {query_str}

I have gathered information from the following sources:

"""

    for idx, item in enumerate(extracted_data, 1):
        prompt += f"SOURCE {idx}: {item['title']} ({item['url']})\n"
        prompt += f"CONTENT: {item['content'][:1500]}...\n\n"  # Trimmed to avoid token limits

    # Add format-specific instructions if writing to a document
    if write:
        format_instructions = {
            'text': 'Write this as a comprehensive, in-depth plain text document in essay format without any special formatting. The document should be at least 1200-1500 words and thoroughly cover all aspects of the topic. Include a numbered references section at the end with the full URL for each reference.',
            
            'markdown': 'Write this as a comprehensive, in-depth professional academic essay in markdown format. The document should be at least 1200-1500 words and thoroughly explore all aspects of the topic. Use rich markdown features like headings, paragraphs, bullet points, tables, and emphasis for a well-structured document. Include at least 5-7 distinct sections with proper headings. Use numbered citations in square brackets [1] when referencing sources. Include a "## References" section at the end with a numbered list of all sources used, formatted as proper markdown links that include both the title and clickable URL for each source, e.g., "1. [Source Title](http://source-url.com)".',
            
            'html': 'Write this as a comprehensive, in-depth professional academic essay in HTML format. The document should be at least 1200-1500 words and thoroughly explore all aspects of the topic. Use appropriate HTML elements for structure, including headings (h1-h3), paragraphs, lists, and minimal styling. Include at least 5-7 distinct sections with proper headings. Use numbered citations in square brackets [1] when referencing sources. Include a "References" section at the end with a numbered list of all sources used, formatted as proper HTML links, e.g., "<li>1. <a href=\'http://source-url.com\'>Source Title</a></li>".'
        }[format]
        
        prompt += f"""
Based on these sources, provide a comprehensive, thorough, and detailed essay answering the original query: "{query_str}"

Important formatting instructions:
1. Write an extensive, in-depth document (minimum 1200-1500 words) that thoroughly covers all aspects of the topic
2. Structure with a proper introduction, at least 5-7 distinct content sections, and a conclusion
3. Include all relevant facts, details, and nuances from the sources
4. If sources contradict each other, analyze the contradictions and different perspectives
5. Use numbered citations in square brackets [1] to reference sources within the text
6. Place ALL references in a dedicated "References" section at the END of the document
7. For each reference, include BOTH the title AND a clickable link to the source URL
8. Do NOT include inline hyperlinks throughout the main text body
9. If information is incomplete, acknowledge limitations and suggest areas for further research

{format_instructions}

This document will be used for professional/academic purposes, so maintain a formal tone, thorough analysis, and proper citation format.
"""
    else:
        prompt += f"""
Based on these sources, provide a comprehensive answer to the original query: "{query_str}"
Include relevant facts and details from the sources. If the sources contradict each other, mention this.
If the information is incomplete or the sources don't fully answer the question, acknowledge this.
Do not include markdown formatting in your response, just use plain text.
"""

    click.echo("🧠 Analyzing collected information...")
    
    # Get the LLM instance
    llm = get_llm()
    
    try:
        # Generate content - use professional mode for document generation
        professional_mode = write  # Use professional mode when generating a document
        response = asyncio.run(llm.generate_response(prompt, professional_mode=professional_mode))
        
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
                filename = 'research_' + '_'.join(words) + ext
                # Use the .cliche/files/docs directory
                output_dir = get_output_dir('docs')
                file_path = str(output_dir / filename)
            else:
                # Make sure filename has correct extension
                if not any(filename.endswith(e) for e in ['.txt', '.md', '.html']):
                    filename += ext
                
                # Use specified filename, but ensure it's in the right directory
                if os.path.dirname(filename):
                    # If a full path is provided, use it
                    file_path = filename
                else:
                    # Otherwise, put it in the docs directory
                    output_dir = get_output_dir('docs')
                    file_path = str(output_dir / filename)
            
            # Ensure HTML has proper structure
            if format == 'html' and not response.strip().startswith('<!DOCTYPE html>'):
                response = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research: {query_str}</title>
</head>
<body>
{response}
</body>
</html>"""
            
            # Save to file
            save_text_to_file(response, file_path)
            click.echo(f"✅ Research document saved to: {file_path}")
        else:
            # Display the response in terminal
            click.echo("\n" + "=" * 60)
            click.echo("📊 RESEARCH RESULTS")
            click.echo("=" * 60)
            click.echo(f"\n💡 {response}\n")
            click.echo("=" * 60)
            click.echo(f"Sources: {len(extracted_data)} websites analyzed")
            click.echo("=" * 60)
        
        return 0  # Return success code
        
    except AttributeError as e:
        click.echo("❌ Error: Provider not properly configured")
        return 1  # Return error code
    except Exception as e:
        click.echo(f"❌ Error generating response: {str(e)}")
        return 1  # Return error code

if __name__ == "__main__":
    research()
