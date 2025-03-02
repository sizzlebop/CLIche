"""General-purpose extractor for any website."""
import os
import re
import logging
from typing import Optional, Dict, Any, List, Union
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from pathlib import Path
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CrawlResult

# Import specific models to reduce dependencies
from ..models.data_models import ScrapedData, ExtractionResult, ScrapedImage
from ..utils.html_processing import clean_html, is_element_node, has_attribute, is_relevant_content
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
        
        # Initialize crawl4ai
        try:
            # Default crawler config
            crawler_config = CrawlerRunConfig(
                workers=2,  # Try just 'workers' without 'num_' prefix
                request_timeout=15,
                handle_js=True,
                handle_forms=False,
                max_depth=1,
                max_pages=1
            )
            self.web_crawler = AsyncWebCrawler(crawler_config)
            self.logger.info("Initialized crawl4ai crawler")
        except Exception as e:
            self.logger.warning(f"Failed to initialize crawl4ai: {str(e)}")
            self.web_crawler = None

    def can_handle(self, url: str) -> bool:
        """This extractor can handle any URL as a fallback."""
        return True

    async def extract(self, url: str, topic: Optional[str] = None,
                     include_images: bool = False, max_images: int = 10,
                     min_size: int = 100, image_dir: Optional[str] = None) -> ExtractionResult:
        """Extract content from any website."""
        try:
            self.logger.info(f"Extracting content from: {url}")
            
            # Get HTML content
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Get title using dedicated method
            title = self._extract_title(soup)
            
            description = ""
            extracted_content = ""
            links = []
            metadata = {
                "source": "general",
                "domain": urlparse(url).netloc,
                "extraction_date": datetime.now().isoformat()
            }
            
            # Try crawl4ai first if available
            if self.web_crawler:
                try:
                    self.logger.info("Attempting extraction with crawl4ai")
                    results = await self.web_crawler.crawl(url, use_browser=True)
                    
                    if results and len(results) > 0 and results[0].content:
                        result = results[0]
                        content_html = result.content
                        crawl_url = result.url
                        
                        # Process the HTML content
                        soup = BeautifulSoup(content_html, 'lxml')
                        
                        # Clean HTML to remove unwanted elements
                        clean_html(soup)
                        
                        # Find main content element
                        main_content_elem = self._find_main_content(soup, topic)
                        
                        # Extract description
                        description = self._extract_description(soup, main_content_elem)
                        
                        # Extract main content as markdown
                        extracted_content = self._extract_content_as_markdown(main_content_elem)
                        
                        # Extract links for further crawling
                        # Get links from crawl4ai results
                        for result in results:
                            if result.links:
                                for link in result.links:
                                    if link not in links:
                                        links.append(link)
                        
                        self.logger.info(f"Successfully extracted with crawl4ai: {len(extracted_content)} chars")
                        
                        # Add crawl4ai metadata
                        metadata["extraction_method"] = "crawl4ai"
                        metadata["js_rendered"] = True
                    else:
                        self.logger.warning("crawl4ai returned empty results, falling back to standard extraction")
                        raise ValueError("Empty crawl4ai results")
                except Exception as e:
                    self.logger.warning(f"crawl4ai extraction failed: {str(e)}, falling back to standard extraction")
                    # Fall back to standard extraction
                    title, description, extracted_content, links = await self._extract_with_requests(url, topic)
                    metadata["extraction_method"] = "requests"
                    metadata["js_rendered"] = False
            else:
                # If crawl4ai is not available, use standard extraction
                self.logger.info("crawl4ai not available, using standard extraction")
                title, description, extracted_content, links = await self._extract_with_requests(url, topic)
                metadata["extraction_method"] = "requests"
                metadata["js_rendered"] = False
            
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
            enhanced_data = scraped_data
            if hasattr(self, 'llm') and self.llm and not os.environ.get("CLICHE_NO_LLM"):
                try:
                    # Convert to dict for enhancement
                    data_dict = scraped_data.dict() if hasattr(scraped_data, 'dict') else scraped_data.to_dict()
                    
                    # Enhance with LLM
                    enhanced_dict = await enhance_content_with_llm(
                        content=data_dict,
                        topic=topic,
                        provider=self.llm
                    )
                    
                    # Create new ScrapedData from enhanced dict
                    enhanced_data = ScrapedData(
                        url=enhanced_dict.get('url', url),
                        title=enhanced_dict.get('title', title),
                        description=enhanced_dict.get('description', description),
                        main_content=enhanced_dict.get('main_content', extracted_content),
                        images=enhanced_dict.get('images', images),
                        metadata=enhanced_dict.get('metadata', metadata)
                    )
                    self.logger.info("Successfully enhanced content with LLM")
                except Exception as e:
                    self.logger.warning(f"Error creating enhanced data: {str(e)}")
                    # Fall back to original data
            
            return ExtractionResult(
                success=True,
                data=enhanced_data,
                links=links[:50]  # Limit number of links to prevent overwhelm
            )
        
        except Exception as e:
            self.logger.error(f"Error in general extraction: {str(e)}")
            return ExtractionResult(
                success=False,
                error=f"General extraction failed: {str(e)}"
            )
    
    async def _extract_with_requests(self, url: str, topic: Optional[str] = None) -> tuple:
        """Extract content using standard requests and BeautifulSoup."""
        self.logger.info(f"Using standard extraction for {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; CLIche/1.0;)',
            'Accept': 'text/html,application/xhtml+xml,application/xml'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Clean HTML
        clean_html(soup)
        
        # Get title
        title = self._extract_title(soup)
        
        # Find main content
        main_content_elem = self._find_main_content(soup, topic)
        
        # Extract description
        description = self._extract_description(soup, main_content_elem)
        
        # Extract main content as markdown
        content_text = self._extract_content_as_markdown(main_content_elem)
        
        # Extract links for further crawling
        links = self._extract_links(main_content_elem, url)
        
        return title, description, content_text, links

    def _find_main_content(self, soup: BeautifulSoup, topic: Optional[str] = None) -> BeautifulSoup:
        """Find the main content element in a page."""
        # Try common content selectors
        for selector in ['article', 'main', '#content', '.content', '.article', '.post', '.entry', '.blog-post']:
            element = soup.select_one(selector)
            if element and is_relevant_content(element.get_text(strip=True), topic):
                return element
        
        # If topic is provided, try to find the most relevant section
        if topic:
            topic_words = set(re.findall(r'\w+', topic.lower()))
            best_score = 0
            best_element = None
            
            for element in soup.find_all(['div', 'section', 'article']):
                if not is_element_node(element):
                    continue
                    
                text = element.get_text(strip=True).lower()
                element_words = set(re.findall(r'\w+', text))
                
                # Count matching words
                match_score = len(topic_words.intersection(element_words))
                
                # Higher score wins
                if match_score > best_score:
                    best_score = match_score
                    best_element = element
                    
            if best_element:
                return best_element
        
        # Default to body if no better element is found
        return soup.body or soup

    def _extract_description(self, soup: BeautifulSoup, main_content: BeautifulSoup) -> str:
        """Extract description from meta tags or first paragraph."""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
            
        # Try OpenGraph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content']
            
        # Try first paragraph
        if main_content:
            first_p = main_content.find('p')
            if first_p:
                desc = first_p.get_text(strip=True)
                if desc:
                    return desc
        
        # Fallback to first 200 chars of main content
        if main_content:
            return main_content.get_text(strip=True)[:200]
            
        return ""

    def _extract_content_as_markdown(self, element: BeautifulSoup) -> str:
        """Extract content from an element and convert to markdown format."""
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
                
                # Get all elements until next heading
                current = heading.next_sibling
                while current and not (is_element_node(current) and current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    if not is_element_node(current):
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
                    elif current.name == 'pre' or current.name == 'code':
                        code = current.get_text()
                        if code:
                            content.append(f"```\n{code}\n```\n\n")
                    elif current.name == 'table':
                        table_md = self._extract_table_as_markdown(current)
                        if table_md:
                            content.append(f"{table_md}\n\n")
                    elif current.name == 'blockquote':
                        quote = current.get_text(strip=True)
                        if quote:
                            quoted_lines = [f"> {line}" for line in quote.split('\n')]
                            content.append('\n'.join(quoted_lines) + '\n\n')
                    elif current.name == 'img' and has_attribute(current, 'src'):
                        alt = current.get('alt', '')
                        src = current.get('src', '')
                        if src:
                            content.append(f"![{alt}]({src})\n\n")
                            
                    current = current.next_sibling
        else:
            # No headings, just extract paragraphs directly
            for p in element.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    content.append(f"{text}\n\n")
                    
        # If still no content, get all text
        if not content:
            content = [element.get_text(strip=True)]
            
        return ''.join(content)

    def _extract_links(self, element: BeautifulSoup, base_url: str) -> List[str]:
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