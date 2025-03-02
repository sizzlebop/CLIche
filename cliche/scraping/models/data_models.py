"""Data models for web scraping functionality."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ScrapedImage(BaseModel):
    """Model for scraped image data."""
    url: str = Field(..., description="Original URL of the image")
    local_path: Optional[str] = Field(None, description="Local path where image is saved")
    alt_text: str = Field("", description="Alternative text for the image")
    caption: str = Field("", description="Caption or description of the image")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    position_index: Optional[int] = Field(None, description="Position index in the document")
    source_url: Optional[str] = Field(None, description="URL of the page where image was found")
    file_type: Optional[str] = Field(None, description="Image file type/format")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'url': self.url,
            'local_path': self.local_path,
            'alt_text': self.alt_text,
            'caption': self.caption,
            'width': self.width,
            'height': self.height,
            'position_index': self.position_index,
            'source_url': self.source_url,
            'file_type': self.file_type
        }

class ScrapedData(BaseModel):
    """Model for scraped web content."""
    url: str = Field(..., description="Source URL of the content")
    title: str = Field(..., description="Title of the page")
    description: str = Field(..., description="A detailed summary of the page content")
    main_content: str = Field(..., description="Complete and comprehensive content of the page")
    images: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Images extracted from the page")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the content was scraped")

class CrawlerConfig(BaseModel):
    """Configuration for the crawler."""
    max_depth: int = Field(0, description="Maximum crawl depth")
    max_pages: int = Field(1, description="Maximum pages to crawl")
    max_concurrent: int = Field(3, description="Maximum concurrent requests")
    follow_links: bool = Field(False, description="Whether to follow links")
    same_domain_only: bool = Field(True, description="Only crawl same domain")
    topic: Optional[str] = Field(None, description="Topic for filtering")
    request_timeout: int = Field(30, description="Request timeout in seconds")
    handle_js: bool = Field(False, description="Handle JavaScript")

class ExtractionResult(BaseModel):
    """Result of content extraction."""
    data: Optional[ScrapedData] = Field(None, description="Extracted content if successful")
    links: List[str] = Field(default_factory=list, description="Discovered links")
    success: bool = Field(False, description="Whether extraction was successful")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    retry_count: int = Field(0, description="Number of retry attempts made")

class ExtractionStrategy(BaseModel):
    """Base model for content extraction strategies."""
    name: str = Field(..., description="Name of the extraction strategy")
    description: str = Field(..., description="Description of the strategy")
    site_patterns: List[str] = Field(..., description="URL patterns this strategy handles")

    def can_handle(self, url: str) -> bool:
        """Check if this strategy can handle the given URL."""
        return any(pattern in url.lower() for pattern in self.site_patterns)