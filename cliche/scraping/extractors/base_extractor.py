"""Base extractor class for content extraction."""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..models.data_models import ExtractionResult, ScrapedData

class BaseExtractor:
    """Base class for content extractors."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.logger = logging.getLogger(__name__)
        self.llm = None
    
    async def extract(
        self,
        url: str,
        topic: Optional[str] = None,
        include_images: bool = False,
        max_images: int = 10,
        min_image_size: int = 100,
        image_dir: Optional[Path] = None,
        use_llm: bool = True
    ) -> ExtractionResult:
        """Extract content from a URL."""
        raise NotImplementedError("Subclasses must implement extract method")
        
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        return False
        
    async def _fallback_extract_content(self, url: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """Basic fallback extraction when crawl4ai isn't available."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Get the page content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract title
            title = soup.title.get_text() if soup.title else url.split('/')[-1]
            
            # Extract description
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and 'content' in meta_desc.attrs:
                description = meta_desc['content']
            else:
                # Try to extract from first paragraph
                first_p = soup.find('p')
                if first_p:
                    description = first_p.get_text().strip()
            
            # Extract main content
            main_content = ""
            main_element = soup.find(['main', 'article']) or soup.find(id=['content', 'main']) or soup.find(class_=['content', 'main'])
            
            if not main_element:
                main_element = soup.body
            
            if main_element:
                # Clean up unwanted elements
                for unwanted in main_element.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    unwanted.decompose()
                
                # Extract text
                for elem in main_element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                    if elem.name.startswith('h'):
                        level = int(elem.name[1])
                        main_content += f"{'#' * level} {elem.get_text().strip()}\n\n"
                    else:
                        main_content += f"{elem.get_text().strip()}\n\n"
            
            return {
                "url": url,
                "title": title,
                "description": description,
                "main_content": main_content,
                "images": []
            }
        
        except Exception as e:
            self.logger.error(f"Error in fallback extraction: {str(e)}")
            return {
                "url": url,
                "title": "Extraction Failed",
                "description": f"Failed to extract content: {str(e)}",
                "main_content": "",
                "images": []
            } 