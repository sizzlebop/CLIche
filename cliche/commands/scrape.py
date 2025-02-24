import os
import asyncio
import click
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
import html2text

def get_output_filename(url: str) -> str:
    """Generate a filename from the URL."""
    # Remove protocol and domain
    path = url.split('/')[-1] if url.endswith('/') else url.split('/')[-1]
    # Convert to lowercase and replace special chars with underscores
    filename = path.lower().replace(' ', '_').replace('-', '_')
    return f"{filename}.md"

def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs belong to the same domain."""
    domain1 = urlparse(url1).netloc
    domain2 = urlparse(url2).netloc
    return domain1 == domain2

def is_nav_link(content: str, url: str) -> bool:
    """Check if a link appears to be a navigation link."""
    # Common patterns for navigation links
    nav_patterns = [
        'Skip to main content',
        'Open Menu',
        'Open Sidebar',
        'Close Search Bar',
        'Open Search Bar',
        'Select language',
        'Sign up',
        'Log in',
        'Request account',
        'View source',
        'View history',
        'Recent changes',
        'Random page',
        'Help',
        'Special pages',
        'Privacy policy',
        'About',
        'Disclaimers',
        'Powered by',
        'Creative Commons',
        'Tools',
        'Navigation',
        'Personal tools',
        'Namespaces',
        'Views',
        'Search',
        'Wiki Tools',
        'Discussion',
        'Talk:',
        'Special:',
        'File:',
        'User:',
        'Template:',
        'Category:',
        'MediaWiki:',
        'action=edit',
        'action=history',
        'oldid=',
        'diff=',
        'redlink=1'
    ]
    
    # Also check URL patterns
    url_patterns = [
        'Special:',
        'File:',
        'Talk:',
        'User:',
        'Template:',
        'Category:',
        'MediaWiki:',
        'action=edit',
        'action=history',
        'oldid=',
        'diff=',
        'redlink=1'
    ]
    
    # Check if any pattern matches the content
    if any(pattern.lower() in content.lower() for pattern in nav_patterns):
        return True
        
    # Check if any pattern matches the URL
    if any(pattern.lower() in url.lower() for pattern in url_patterns):
        return True
        
    return False

def is_relevant_link(text: str, url: str, topic: str | None = None) -> bool:
    """Check if a link is relevant to the topic we're interested in."""
    if not topic:
        return True
        
    # Convert everything to lowercase for comparison
    text = text.lower()
    topic = topic.lower()
    url = url.lower()
    
    # Split topic into words for more flexible matching
    topic_words = set(topic.split())
    
    # Check if any topic word appears in the text or URL
    return any(word in text or word in url for word in topic_words)

def extract_links_from_markdown(content: str, base_url: str, topic: str | None = None) -> list[str]:
    """Extract markdown links and convert them to full URLs."""
    links = []
    lines = content.split('\n')
    for line in lines:
        # Skip navigation-like links
        if is_nav_link(line, base_url):
            continue
            
        # Look for markdown links [text](url)
        start = 0
        while True:
            start = line.find('](', start)
            if start == -1:
                break
            end = line.find(')', start)
            if end == -1:
                break
                
            # Extract the link text and URL
            text_start = line.rfind('[', 0, start)
            if text_start == -1:
                start = end + 1
                continue
                
            link_text = line[text_start+1:start]
            url = line[start+2:end].strip()
            
            # Skip navigation links
            if is_nav_link(link_text, base_url):
                start = end + 1
                continue
                
            # Skip irrelevant links if we have a topic
            if not is_relevant_link(link_text, url, topic):
                start = end + 1
                continue
                
            # Convert relative URLs to absolute
            if url.startswith('/'):
                url = urljoin(base_url, url)
            if url.startswith('http'):  # Only keep http(s) URLs
                links.append(url)
            start = end + 1
    return links

async def scrape_page(crawler: AsyncWebCrawler, url: str, base_url: str, visited: set, topic: str | None = None) -> tuple[str, list[str]]:
    """Scrape a single page and return its content and any found links."""
    try:
        config = CrawlerRunConfig(
            page_timeout=60000,  # Wait up to 60 seconds
            wait_until='load',  # Just wait for page load
            scan_full_page=True,  # Get everything
            magic=False,  # Turn off magic mode
            wait_for_images=False,  # Don't wait for images
            excluded_tags=[],  # Don't exclude any tags
            word_count_threshold=0,  # No minimum word count
            exclude_external_links=False,  # Don't exclude external links
            exclude_social_media_links=False,  # Don't exclude social links
            remove_overlay_elements=False  # Don't remove overlays
        )
        
        result = await crawler.arun(url=url, config=config)
        if not result or not result.cleaned_html:
            return "", []
        
        # Convert HTML to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.body_width = 0
        content = h.handle(result.cleaned_html)
        
        # Extract links from markdown content
        links = extract_links_from_markdown(content, base_url, topic)
        
        return content, links
    except Exception as e:
        click.echo(f"⚠️  Error scraping {url}: {str(e)}")
        return "", []

async def async_scrape(url: str, topic: str | None = None):
    """Scrape content from a URL and all its linked pages."""
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.expanduser("~/.cliche/files/scrape")
        os.makedirs(output_dir, exist_ok=True)
        
        visited = set()
        to_visit = [url]
        all_content = []
        
        async with AsyncWebCrawler() as crawler:
            while to_visit and len(visited) < 100:  # Limit to 100 pages max
                current_url = to_visit.pop(0)
                
                if current_url in visited:
                    continue
                    
                click.echo(f"📄 Scraping page {len(visited) + 1}: {current_url}")
                
                content, links = await scrape_page(crawler, current_url, url, visited, topic)
                visited.add(current_url)
                
                if content.strip():  # Only add non-empty content
                    all_content.append(f"# {current_url}\n\n{content}")
                
                # Add new links to visit
                for link in links:
                    if link not in visited and is_same_domain(url, link):
                        to_visit.append(link)
            
            if not all_content:
                click.echo("❌ No content was found to save")
                return
                
            # Save all content
            output_path = os.path.join(output_dir, get_output_filename(url))
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n\n---\n\n".join(all_content))
            
            click.echo(f"\n\n✨ Scraped {len(visited)} pages, saved to {output_path}")
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)

@click.command()
@click.argument('url')
@click.option('--topic', '-t', help='Optional topic to focus on (e.g., "Python Variables")')
def scrape(url: str, topic: str | None = None):
    """Scrape content from a URL and all its linked pages (up to 100 pages).
    
    Optionally provide a --topic to focus on specific content."""
    asyncio.run(async_scrape(url, topic))