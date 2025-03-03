"""General-purpose extractor for any website."""
import os
import re
import logging
from typing import Optional, Dict, Any, List, Union, Tuple
import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
from datetime import datetime
from pathlib import Path
import asyncio
import time
# Restore crawl4ai imports
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Import specific models to reduce dependencies
from ..models.data_models import ScrapedData, ExtractionResult, ScrapedImage
from ..utils.html_processing import clean_html, is_element_node, has_attribute, is_relevant_content, detect_code_language, process_div_content, extract_table_as_markdown
from ..utils.llm_enhancement import enhance_content_with_llm, generate_summary
from cliche.utils.image_scraper import extract_and_download_images_async, ScrapedImage
from .image_extractor import ImageExtractor

class GeneralExtractor:
    """General-purpose content extractor for any website."""

    def __init__(self):
        """Initialize the general extractor."""
        self.logger = logging.getLogger(__name__)
        self.llm = None
        self.web_crawler = None
        self.image_extractor = ImageExtractor()  # Initialize image extractor
        self.char_limit = 1000000  # Much higher limit (1 million chars) - effectively unlimited
        
        # We'll initialize the crawler when needed, not here

    def can_handle(self, url: str) -> bool:
        """This extractor can handle any URL as a fallback."""
        return True

    async def extract(self, url: str, topic: Optional[str] = None,
                     include_images: bool = False, max_images: int = 10,
                     min_size: int = 100, image_dir: Optional[str] = None,
                     use_llm: bool = True) -> ExtractionResult:
        """Extract content from any website."""
        try:
            self.logger.info(f"Extracting content from: {url}")
            
            # Set LLM usage from parameter
            if not use_llm and "CLICHE_NO_LLM" not in os.environ:
                os.environ["CLICHE_NO_LLM"] = "1"
            elif use_llm and "CLICHE_NO_LLM" in os.environ:
                del os.environ["CLICHE_NO_LLM"]
            
            # Initialize variables
            title = ""
            description = ""
            extracted_content = ""
            links = []
            metadata = {
                "source": "general",
                "domain": urlparse(url).netloc,
                "extraction_date": datetime.now().isoformat()
            }
            
            # ----- Use the same crawl4ai implementation as research.py -----
            try:
                # Initialize crawl4ai properly like in research.py
                print("[INIT].... → Crawl4AI 0.4.248")
                
                # Create a new crawler instance for each extraction
                crawler = AsyncWebCrawler()
                
                # Print like in research.py
                print(f"🌐 Scraping: {url}")
                
                # Track time like in research.py
                start_time = time.time()
                
                # Fetch the URL
                print(f"[FETCH]... ↓ {url}... | Status: Pending")
                
                # Use arun to crawl the URL
                result = await crawler.arun(
                    url=url,
                    use_browser=True,
                    handle_js=True
                )
                
                fetch_time = time.time() - start_time
                print(f"[FETCH]... ↓ {url}... | Status: True | Time: {fetch_time:.2f}s")
                
                # Process the result
                scrape_start = time.time()
                print(f"[SCRAPE].. ◆ Processing {url}...")
                
                # Extract the content
                if result and hasattr(result, 'content') and result.content:
                    soup = BeautifulSoup(result.content, 'lxml')
                    
                    # Get title
                    title = result.title if hasattr(result, 'title') else self._extract_title(soup)
                    
                    # Clean HTML
                    clean_html(soup)
                    
                    # Find main content element
                    main_content_elem = self._find_main_content(soup, topic)
                    
                    # Extract description
                    description = result.description if hasattr(result, 'description') else self._extract_description(soup, main_content_elem)
                    
                    # Extract content as markdown with increased character limit
                    extracted_content = self._extract_content_as_markdown(main_content_elem)
                    
                    # Limit content to char_limit
                    if len(extracted_content) > self.char_limit:
                        extracted_content = extracted_content[:self.char_limit]
                    
                    # Extract links
                    links = self._extract_links(main_content_elem, url)
                    
                    scrape_time = time.time() - scrape_start
                    print(f"[SCRAPE].. ◆ Processed {url}... | Time: {int(scrape_time * 1000)}ms")
                    
                    total_time = time.time() - start_time
                    print(f"[COMPLETE] ● {url}... | Status: True | Total: {total_time:.2f}s")
                    print(f"✅ Content extracted: {len(extracted_content)} chars")
                    
                    metadata["extraction_method"] = "crawl4ai"
                    metadata["js_rendered"] = True
                    metadata["extraction_time"] = f"{total_time:.2f}s"
                else:
                    print(f"[ERROR]... × {url}... | Error: Empty result")
                    raise ValueError("Empty crawl4ai results")
                    
            except Exception as e:
                self.logger.warning(f"crawl4ai extraction failed: {str(e)}, falling back to standard extraction")
                print(f"[ERROR]... × {url}... | Error: {str(e)}")
                
                # Fall back to standard extraction
                title, description, extracted_content, links = await self._extract_with_requests(url, topic)
                metadata["extraction_method"] = "requests"
                metadata["js_rendered"] = False
            
            # Get HTML for image extraction (if we didn't already)
            soup = None
            if include_images:
                if metadata["extraction_method"] != "crawl4ai":
                    # Get the page for image extraction if we didn't use crawl4ai
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract images if requested
            images = []
            if include_images:
                try:
                    # Use ImageExtractor for image extraction
                    output_dir = Path(image_dir) if image_dir else None
                    html_content = str(soup) if soup else ""
                    images = await self.image_extractor.extract_images(
                        html_content=html_content,
                        base_url=url,
                        max_images=max_images,
                        min_size=min_size,
                        output_dir=output_dir,
                        topic=topic
                    )
                    self.logger.info(f"Extracted {len(images)} images")
                    
                    # Debug output to match original
                    for idx, img in enumerate(images):
                        if hasattr(img, 'to_dict'):
                            img_dict = img.to_dict()
                        else:
                            img_dict = img
                        self.logger.debug(f"Image {idx+1}: URL={img_dict.get('url')}, local_path={img_dict.get('local_path')}")
                        
                except Exception as e:
                    self.logger.error(f"Error extracting images: {str(e)}")
            
            # Create scraped data
            scraped_data = ScrapedData(
                url=url,
                title=title,
                description=description,
                main_content=extracted_content,
                images=[img.to_dict() if hasattr(img, 'to_dict') else img for img in images],
                metadata=metadata
            )
            
            # Use LLM to enhance the content if available
            if hasattr(self, 'llm') and self.llm and not os.environ.get("CLICHE_NO_LLM"):
                try:
                    # Convert to dict for enhancement
                    data_dict = scraped_data.dict() if hasattr(scraped_data, 'dict') else scraped_data.model_dump()
                    
                    # Enhance with LLM
                    enhanced_dict = await enhance_content_with_llm(
                        content=data_dict,
                        topic=topic,
                        provider=self.llm
                    )
                    
                    if enhanced_dict:
                        # Create new ScrapedData from enhanced dict
                        scraped_data = ScrapedData(
                            url=enhanced_dict.get('url', url),
                            title=enhanced_dict.get('title', title),
                            description=enhanced_dict.get('description', description),
                            main_content=enhanced_dict.get('main_content', extracted_content),
                            images=enhanced_dict.get('images', images),
                            metadata=metadata
                        )
                except Exception as e:
                    self.logger.warning(f"LLM enhancement failed: {str(e)}")
            
            return ExtractionResult(
                success=True,
                data=scraped_data,
                links=links
            )
            
        except Exception as e:
            self.logger.error(f"Error in general extraction: {str(e)}")
            # Print stack trace for debugging like original
            import traceback
            if os.environ.get("CLICHE_DEBUG"):
                print(f"DEBUG: Extraction error details: {traceback.format_exc()}")
            return ExtractionResult(
                success=False,
                error=f"General extraction failed: {str(e)}"
            )
    
    async def _extract_with_requests(self, url: str, topic: Optional[str] = None) -> Tuple[str, str, str, List[str]]:
        """Extract content using standard requests and BeautifulSoup when crawl4ai fails."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; CLIche/1.0; +http://github.com/sizzlebop/cliche)',
                'Accept': 'text/html,application/xhtml+xml,application/xml'
            }
            
            # Get the page
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Get title
            title = self._extract_title(soup)
            
            # Find main content
            main_content_elem = self._find_main_content(soup, topic)
            
            # Extract description
            description = self._extract_description(soup, main_content_elem)
            
            # Extract content as markdown
            extracted_content = self._extract_content_as_markdown(main_content_elem)
            
            # Extract links
            links = self._extract_links(main_content_elem, url)
            
            return title, description, extracted_content, links
            
        except Exception as e:
            self.logger.error(f"Error in fallback extraction: {str(e)}")
            return "Extraction Failed", f"Failed to extract content: {str(e)}", "", []

    def _find_main_content(self, soup: BeautifulSoup, topic: Optional[str] = None) -> Tag:
        """Find the main content area of the page."""
        # Try common selectors for main content
        selectors = [
            'main', 'article', '#content', '#main', '.content', '.main',
            '.post', '.entry', '.article', '[role="main"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and len(element.get_text(strip=True)) > 100:
                return element
        
        # Fallback to using the body with unwanted elements removed
        if soup.body:
            # Create a copy to avoid modifying the original
            body_copy = BeautifulSoup(str(soup.body), 'lxml').body
            
            # Remove unwanted elements
            for selector in ['header', 'footer', 'nav', 'aside', '.sidebar', '#sidebar']:
                for element in body_copy.select(selector):
                    element.decompose()
                
            return body_copy
        
        # Last resort - just use whatever we have
        return soup

    def _extract_description(self, soup: BeautifulSoup, main_content: Tag) -> str:
        """Extract a description from the page."""
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content')
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc.get('content')
        
        # Try first paragraph
        if main_content:
            first_p = main_content.find('p')
            if first_p and first_p.get_text(strip=True):
                return first_p.get_text(strip=True)
        
        # Fallback to using first 200 chars of content
        if main_content:
            return main_content.get_text(strip=True)[:200]
        
        return ""

    def _extract_links(self, element: Tag, base_url: str) -> List[str]:
        """Extract links from content."""
        if not element:
            return []
        
        links = []
        base_domain = urlparse(base_url).netloc
        
        for a in element.find_all('a', href=True):
            href = a.get('href', '')
            if not href or href.startswith('#'):
                continue
            
            # Resolve relative URLs
            if not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
            
            # Only include links from the same domain
            link_domain = urlparse(href).netloc
            if link_domain == base_domain:
                links.append(href)
            
        return links

    def _extract_content_as_markdown(self, element: Tag) -> str:
        """Extract content from HTML and convert to markdown format."""
        if not element:
            return ""
        
        content_text = []
        
        # First check for headings to determine if the page has structure
        headings = element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        has_structure = len(headings) > 1
        
        # Create a map of heading levels
        heading_map = {}
        for idx, h_tag in enumerate(headings):
            level = int(h_tag.name[1])
            heading_map[h_tag] = level
        
        # If page has structured headings, extract content section by section
        if has_structure:
            self.logger.info(f"Found {len(headings)} headings for structured extraction")
            
            # Extract all content based on headings
            for idx, h_tag in enumerate(headings):
                heading_level = heading_map[h_tag]
                heading_text = h_tag.get_text(strip=True)
                content_text.append(f"{'#' * heading_level} {heading_text}\n\n")
                
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
                                content_text.append(f"{text}\n\n")
                        elif current.name in ['ul', 'ol']:
                            for li in current.find_all('li', recursive=True):
                                li_text = li.get_text(strip=True)
                                if li_text:
                                    content_text.append(f"* {li_text}\n")
                            content_text.append("\n")
                        elif current.name in ['pre', 'code']:
                            code_text = current.get_text(strip=True)
                            if code_text:
                                lang = self._detect_code_language(current, code_text)
                                content_text.append(f"```{lang}\n{code_text}\n```\n\n")
                        elif current.name == 'table':
                            table_text = self._extract_table_as_markdown(current)
                            if table_text:
                                content_text.append(f"{table_text}\n\n")
                        elif current.name == 'div':
                            div_content = self._process_div_content(current)
                            if div_content:
                                content_text.append(f"{div_content}\n\n")
                    
                    # Move to next element
                    current = current.next_sibling
        else:
            # No structured headings found, extract all content in sequence
            for child in element.children:
                if hasattr(child, 'name') and child.name:
                    if child.name == 'p':
                        text = child.get_text(strip=True)
                        if text:
                            content_text.append(f"{text}\n\n")
                    elif child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        level = int(child.name[1])
                        text = child.get_text(strip=True)
                        if text:
                            content_text.append(f"{'#' * level} {text}\n\n")
                    elif child.name in ['ul', 'ol']:
                        for li in child.find_all('li', recursive=True):
                            li_text = li.get_text(strip=True)
                            if li_text:
                                content_text.append(f"* {li_text}\n")
                        content_text.append("\n")
                    elif child.name in ['pre', 'code']:
                        code_text = child.get_text(strip=True)
                        if code_text:
                            lang = self._detect_code_language(child, code_text)
                            content_text.append(f"```{lang}\n{code_text}\n```\n\n")
                    elif child.name == 'table':
                        table_text = self._extract_table_as_markdown(child)
                        if table_text:
                            content_text.append(f"{table_text}\n\n")
                    elif child.name == 'div':
                        div_content = self._process_div_content(child)
                        if div_content:
                            content_text.append(f"{div_content}\n\n")
        
        return "".join(content_text)

    def _detect_code_language(self, element: Tag, code_text: str) -> str:
        """Detect programming language from code element or content."""
        return detect_code_language(element, code_text)

    def _process_div_content(self, div: Tag) -> str:
        """Process content in a div element."""
        return process_div_content(div)

    def _extract_table_as_markdown(self, table: Tag) -> str:
        """Convert an HTML table to markdown format."""
        return extract_table_as_markdown(table)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML content."""
        # Try article h1 first
        if article_h1 := soup.select_one('article h1, .content h1'):
            return article_h1.get_text(strip=True)
        
        # Try any h1
        if h1 := soup.select_one('h1'):
            return h1.get_text(strip=True)
        
        # Try title tag
        if title := soup.title:
            return title.get_text(strip=True)
        
        return "Web Page"