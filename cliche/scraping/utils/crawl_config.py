"""Utilities for configuring crawl4ai."""
from typing import Optional, Dict, Any
from crawl4ai import CrawlerRunConfig

def get_crawl_config(
    depth: int = 1,
    max_pages: int = 5,
    include_js: bool = True,
    num_workers: int = 2,
    timeout: int = 30
) -> CrawlerRunConfig:
    """
    Get a configured crawl4ai CrawlerRunConfig.
    
    Args:
        depth: Maximum depth to crawl
        max_pages: Maximum number of pages to crawl
        include_js: Whether to use JavaScript rendering
        num_workers: Number of parallel workers
        timeout: Request timeout in seconds
        
    Returns:
        CrawlerRunConfig object
    """
    return CrawlerRunConfig(
        num_workers=num_workers,
        request_timeout=timeout,
        handle_js=include_js,
        handle_forms=False,  # Usually not needed for content extraction
        max_depth=depth,
        max_pages=max_pages
    ) 