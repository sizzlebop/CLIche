"""Specialized extractor for Wikipedia articles."""
import os
import re
import logging
from typing import Optional, Dict, Any, List, Union
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from pathlib import Path

# Import specific models to reduce dependencies
from ..models.data_models import ScrapedData, ExtractionResult, ScrapedImage
from .image_extractor import ImageExtractor
from .base_extractor import BaseExtractor

class WikipediaExtractor(BaseExtractor):
    """Specialized content extractor for Wikipedia articles."""

    def __init__(self):
        """Initialize the Wikipedia extractor."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # For LLM integration later
        self.llm = None
        self.image_extractor = ImageExtractor()

    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        parsed_url = urlparse(url)
        return "wikipedia.org" in parsed_url.netloc.lower()

    async def extract(self, url: str, topic: Optional[str] = None,
                     include_images: bool = False, max_images: int = 10,
                     min_size: int = 100, image_dir: Optional[str] = None,
                     use_llm: bool = True) -> ExtractionResult:
        """Extract content from a Wikipedia article."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; CLIche/1.0; +http://github.com/sizzlebop/cliche)',
                'Accept': 'text/html,application/xhtml+xml,application/xml'
            }
            
            # Set LLM usage from parameter
            if not use_llm and "CLICHE_NO_LLM" not in os.environ:
                os.environ["CLICHE_NO_LLM"] = "1"
            elif use_llm and "CLICHE_NO_LLM" in os.environ:
                del os.environ["CLICHE_NO_LLM"]
            
            self.logger.info(f"📚 Fetching Wikipedia article: {url}")
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Remove unwanted elements
            for selector in ['.mw-editsection', '.mw-empty-elt', '.mw-headline']:
                for element in soup.select(selector):
                    element.decompose()
            
            # Get title from firstHeading or title
            title = soup.select_one('#firstHeading')
            if title:
                title = title.get_text(strip=True)
            else:
                title = soup.title.get_text() if soup.title else "Wikipedia Article"
                # Clean up title (remove " - Wikipedia" suffix)
                title = re.sub(r'\s*-\s*Wikipedia.*$', '', title)
            
            # Get main content
            main_content_div = soup.select_one('#mw-content-text')
            if not main_content_div:
                return ExtractionResult(
                    success=False,
                    error="Could not find main content"
                )
            
            # Extract text
            # Get first paragraph for description
            description = ""
            first_para = main_content_div.select_one('.mw-parser-output > p')
            if first_para:
                description = first_para.get_text(strip=True)
            else:
                # Use the first 200 characters as a description
                description = main_content_div.get_text(strip=True)[:200]
            
            # Process the content
            main_content = self._extract_main_content(main_content_div)
            
            # Extract images if requested
            images = []
            if include_images:
                try:
                    # Use ImageExtractor for image extraction
                    output_dir = Path(image_dir) if image_dir else None
                    images = await self.image_extractor.extract_images(
                        html_content=str(soup),
                        base_url=url,
                        max_images=max_images,
                        min_size=min_size,
                        output_dir=output_dir,
                        topic=topic
                    )
                    self.logger.info(f"Extracted {len(images)} images")
                except Exception as e:
                    self.logger.error(f"Error extracting images: {str(e)}")
            
            # Extract links for further crawling
            links = []
            # Only collect links to Wikipedia articles
            for a in main_content_div.find_all('a', href=True):
                href = a.get('href', '')
                if not href or href.startswith('#'):
                    continue
                    
                # Resolve relative URLs
                if href.startswith('/wiki/'):
                    href = f"https://{urlparse(url).netloc}{href}"
                elif not href.startswith(('http://', 'https://')):
                    continue
                    
                # Keep only links to Wikipedia articles
                if "wikipedia.org" in href and "/wiki/" in href:
                    # Skip non-article namespaces
                    if any(ns in href for ns in [
                        "/wiki/File:", "/wiki/Wikipedia:", "/wiki/Template:", 
                        "/wiki/Help:", "/wiki/Category:", "/wiki/Portal:"
                    ]):
                        continue
                    links.append(href)
            
            # Create a ScrapedData object
            scraped_data = ScrapedData(
                url=url,
                title=title,
                description=description,
                main_content=main_content,
                images=[img.to_dict() if hasattr(img, 'to_dict') else img for img in images],
                metadata={
                    "source": "wikipedia",
                    "domain": urlparse(url).netloc,
                    "extraction_date": datetime.now().isoformat()
                }
            )
            
            # Enhance with LLM if available
            if self.llm and not os.environ.get("CLICHE_NO_LLM"):
                try:
                    enhanced_data = await enhance_content_with_llm(
                        content=scraped_data.dict(),
                        topic=topic,
                        provider=self.llm
                    )
                    if enhanced_data:
                        scraped_data = ScrapedData(**enhanced_data)
                except Exception as e:
                    self.logger.warning(f"LLM enhancement failed: {str(e)}")
            
            return ExtractionResult(
                success=True,
                data=scraped_data,
                links=links
            )
        
        except Exception as e:
            self.logger.error(f"Error in Wikipedia extraction: {str(e)}")
            return ExtractionResult(
                success=False,
                error=f"Wikipedia extraction failed: {str(e)}"
            )

    def _extract_main_content(self, main_div: BeautifulSoup) -> str:
        """Extract and format main content."""
        content = []
        
        # Process all main content elements
        for element in main_div.select('.mw-parser-output > *'):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                text = element.get_text(strip=True)
                if text:
                    content.append(f"{'#' * level} {text}\n\n")
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text:
                    content.append(f"{text}\n\n")
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li', recursive=True):
                    text = li.get_text(strip=True)
                    if text:
                        content.append(f"* {text}\n")
                content.append("\n")
            elif element.name in ['pre', 'code']:
                code = element.get_text(strip=True)
                if code:
                    content.append(f"```\n{code}\n```\n\n")
            elif element.name == 'blockquote':
                text = element.get_text(strip=True)
                if text:
                    content.append(f"> {text}\n\n")
        
        return "".join(content)

    def _extract_table_as_markdown(self, table: BeautifulSoup) -> str:
        """Convert an HTML table to markdown format."""
        markdown_table = []
        
        # Extract headers
        headers = []
        for th in table.find_all('th'):
            headers.append(th.get_text(strip=True))
        
        # Use first row if no headers
        if not headers and table.find('tr'):
            headers = [td.get_text(strip=True) for td in table.find('tr').find_all(['td', 'th'])]
        
        if not headers:
            return ""
            
        # Add header row
        markdown_table.append("| " + " | ".join(headers) + " |")
        markdown_table.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Add data rows
        start_idx = 0 if not table.find('th') else 1
        for row in table.find_all('tr')[start_idx:]:
            cells = []
            for cell in row.find_all(['td', 'th']):
                text = cell.get_text(strip=True).replace('|', '\\|')
                cells.append(text)
            if cells:
                markdown_table.append("| " + " | ".join(cells) + " |")
        
        return "\n".join(markdown_table)
