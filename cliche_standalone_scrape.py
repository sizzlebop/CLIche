#!/usr/bin/env python3
"""
Standalone scraper that doesn't depend on the full CLIche framework.
Run this script directly to scrape content from websites.
"""
import os
import sys
import json
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cliche-scrape")

# Simple models for results
class ScrapedData:
    """Model for scraped content."""
    def __init__(self, url, title, description, main_content, images=None, metadata=None):
        self.url = url
        self.title = title
        self.description = description
        self.main_content = main_content
        self.images = images or []
        self.metadata = metadata or {}
        
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "main_content": self.main_content,
            "images": self.images,
            "metadata": self.metadata
        }

# Main functionality
async def scrape_url(url, topic=None, include_images=False, max_images=5):
    """Scrape content from a URL."""
    print(f"Scraping {url}...")
    
    # Determine which extractor to use
    extractor_type = "generic"
    if "wikipedia.org" in url:
        extractor_type = "wikipedia"
    elif "python.org" in url:
        extractor_type = "python"
        
    print(f"Using {extractor_type} extractor")
    
    # Fetch the page
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; CLIche-Standalone/1.0)',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Get title
        title = soup.title.get_text() if soup.title else "Web Page"
        if extractor_type == "wikipedia":
            title = title.split(' - Wikipedia')[0]
            
        # Find main content based on extractor type
        main_div = None
        if extractor_type == "python":
            for selector in ['#content', '.body', '.document', 'article.text']:
                main_div = soup.select_one(selector)
                if main_div:
                    break
        elif extractor_type == "wikipedia":
            main_div = soup.select_one('#mw-content-text')
        else:
            # Generic extractor
            for selector in ['article', 'main', '#content', '.content']:
                main_div = soup.select_one(selector)
                if main_div:
                    break
                    
        # Fallback to body
        if not main_div:
            main_div = soup.body
            
        # Get description
        description = ""
        first_p = main_div.find('p') if main_div else None
        if first_p:
            description = first_p.get_text(strip=True)
        else:
            description = main_div.get_text(strip=True)[:200] if main_div else ""
            
        # Process content
        main_content = extract_content_as_markdown(main_div)
        
        # Create result
        data = ScrapedData(
            url=url,
            title=title,
            description=description,
            main_content=main_content,
            metadata={
                "source": extractor_type,
                "domain": urlparse(url).netloc,
                "extraction_date": datetime.now().isoformat()
            }
        )
        
        return {
            "success": True,
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    
def extract_content_as_markdown(element):
    """Extract content from an element and convert to markdown."""
    if not element:
        return ""
        
    content = []
    
    # Process headings
    headings = element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if headings:
        for heading in headings:
            level = int(heading.name[1])
            text = heading.get_text(strip=True)
            content.append(f"{'#' * level} {text}\n\n")
            
            # Get next elements until next heading
            current = heading.next_sibling
            while current and not (hasattr(current, 'name') and current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                if not hasattr(current, 'name') or not current.name:
                    current = current.next_sibling
                    continue
                    
                if current.name == 'p':
                    text = current.get_text(strip=True)
                    if text:
                        content.append(f"{text}\n\n")
                elif current.name in ['ul', 'ol']:
                    for li in current.find_all('li'):
                        li_text = li.get_text(strip=True)
                        if li_text:
                            content.append(f"* {li_text}\n")
                    content.append("\n")
                    
                current = current.next_sibling
    else:
        # No headings, just extract paragraphs
        for p in element.find_all('p'):
            text = p.get_text(strip=True)
            if text:
                content.append(f"{text}\n\n")
                
    # If still no content, get all text
    if not content:
        content = [element.get_text(strip=True)]
        
    return ''.join(content)

async def save_to_file(data, topic=None):
    """Save extraction data to a file."""
    try:
        # Create output directory
        home_dir = Path.home()
        output_dir = home_dir / "cliche" / "files" / "scrape"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        url = data.url
        domain = urlparse(url).netloc.replace('.', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if topic:
            # Sanitize topic for filename
            topic_clean = ''.join(c if c.isalnum() or c == '_' else '_' for c in topic)
            filename = f"scraped_{domain}_{topic_clean}_{timestamp}.json"
        else:
            filename = f"scraped_{domain}_{timestamp}.json"
            
        output_path = output_dir / filename
        
        # Save to file
        with open(output_path, "w") as f:
            json.dump(data.to_dict(), f, indent=2, default=lambda o: o.isoformat() if isinstance(o, datetime) else None)
            
        print(f"Saved to: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Error saving to file: {str(e)}")
        return None

async def main(args):
    """Main function."""
    # Print header
    print("\n🔍 Cliche Standalone Scraper")
    print("─────────────────────────\n")
    
    # Scrape the URL
    result = await scrape_url(
        url=args.url,
        topic=args.topic,
        include_images=args.include_images,
        max_images=args.max_images
    )
    
    if result["success"]:
        data = result["data"]
        print("✅ Extraction successful!")
        print(f"📗 Title: {data.title}")
        print(f"📝 Description: {data.description[:100]}...")
        print(f"📊 Content length: {len(data.main_content)} characters")
        
        # Save to file
        if not args.no_save:
            print("\n💾 Saving to file...")
            output_path = await save_to_file(data, args.topic)
            
            if output_path:
                print(f"📄 File saved at: {output_path}")
                return 0
            else:
                print("❌ Failed to save file")
                return 1
        return 0
    else:
        print(f"❌ Extraction failed: {result['error']}")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone scraper for CLIche")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("topic", nargs="?", help="Optional topic to focus on")
    parser.add_argument("--include-images", action="store_true", help="Include images in extraction")
    parser.add_argument("--max-images", type=int, default=5, help="Maximum number of images to extract")
    parser.add_argument("--no-save", action="store_true", help="Don't save to file")
    
    args = parser.parse_args()
    
    success = asyncio.run(main(args))
    sys.exit(0 if success else 1) 