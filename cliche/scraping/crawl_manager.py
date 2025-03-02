"""
Advanced crawling functionality for CLIche.
"""
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from pathlib import Path

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from .models.data_models import CrawlerConfig, ExtractionResult
from .extractors.manager import get_extractor_manager

logger = logging.getLogger(__name__)

class CrawlManager:
    """Manager for advanced crawling with multiple extractors."""
    
    def __init__(self):
        """Initialize the crawl manager."""
        self.logger = logging.getLogger(__name__)
        self.extractor_manager = get_extractor_manager()
        self.web_crawler = None
        self.llm = None
        
        try:
            # Use default config with no parameters since API has changed
            crawler_config = CrawlerRunConfig()  # Use defaults
            self.web_crawler = AsyncWebCrawler(crawler_config)
            self.logger.info("Initialized crawl4ai crawler with default settings")
        except Exception as e:
            self.logger.warning(f"Failed to initialize crawl4ai: {str(e)}")
            self.web_crawler = None
    
    def set_llm(self, llm):
        """Set the LLM provider."""
        self.llm = llm
        # Also set it for all extractors
        for extractor in self.extractor_manager.all_extractors():
            extractor.llm = llm
    
    async def crawl_and_extract(
        self, 
        url: str,
        config: CrawlerConfig,
        include_images: bool = False,
        output_dir: Optional[Path] = None,
        topic: Optional[str] = None
    ) -> List[ExtractionResult]:
        """
        Crawl a website and extract content using the appropriate extractors.
        
        Args:
            url: Starting URL for crawling
            config: Configuration for the crawler
            include_images: Whether to extract images
            output_dir: Directory to save images
            topic: Optional topic for organizing content
            
        Returns:
            List of extraction results
        """
        self.logger.info(f"Starting crawl and extract from {url}")
        results = []
        
        # Start with the initial URL
        initial_result = await self._extract_single_url(
            url, 
            include_images=include_images,
            output_dir=output_dir,
            topic=topic
        )
        
        if initial_result and initial_result.success:
            results.append(initial_result)
            
            # If crawling is enabled, crawl additional pages
            if config.max_depth > 0 and config.max_pages > 1:
                additional_results = await self._crawl_additional_pages(
                    initial_result.links,
                    base_url=url,
                    config=config,
                    include_images=include_images,
                    output_dir=output_dir,
                    topic=topic
                )
                results.extend(additional_results)
        
        return results
    
    async def _extract_single_url(
        self, 
        url: str,
        include_images: bool = False,
        output_dir: Optional[Path] = None,
        topic: Optional[str] = None
    ) -> Optional[ExtractionResult]:
        """Extract content from a single URL with original robust extraction approach."""
        try:
            # Check for LLM usage environment variable like in original code
            use_llm = "CLICHE_NO_LLM" not in os.environ and self.llm is not None
            
            # Choose appropriate extractor based on URL patterns
            extractor = self.extractor_manager.get_extractor_for_url(url)
            
            # Extract content
            result = await extractor.extract(
                url=url,
                topic=topic,
                include_images=include_images,
                max_images=20,  # Increased from default 10
                min_size=100,
                image_dir=output_dir,
                use_llm=use_llm
            )
            
            # Apply relevance filtering like original code did
            if topic and result.success and result.data:
                if not self._is_content_relevant(result.data.main_content, topic):
                    self.logger.info(f"Content from {url} not relevant to topic '{topic}'")
                    result.success = False
                    result.error = "Content not relevant to topic"
                    return result
            
            # Enhance with LLM if available and enabled
            if use_llm and self.llm and result.success:
                try:
                    # Use your exact original prompt template
                    await self._enhance_with_llm(result, topic)
                except Exception as e:
                    self.logger.warning(f"LLM enhancement failed: {str(e)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting from {url}: {str(e)}")
            return None
    
    def _is_content_relevant(self, text: str, topic: str = None) -> bool:
        """Check if extracted text is relevant to the topic with improved relevance scoring.
        Direct port from the original code for consistency."""
        # If no topic provided, all content is relevant
        if not topic:
            return True
        
        topic_words = set(topic.lower().split())
        text_lower = text.lower()
        
        # Basic frequency counting
        word_count = 0
        for word in topic_words:
            word_count += text_lower.count(word)
        
        # Weighted by position (earlier mentions matter more)
        position_score = 0
        for word in topic_words:
            pos = text_lower.find(word)
            if pos != -1:
                # Earlier positions get higher scores
                position_score += max(0, 1.0 - (pos / min(1000, len(text_lower))))
        
        # Density score (relevant words per total length)
        density = word_count / max(1, len(text_lower.split()))
        
        # Combined score - using your exact formula
        relevance_score = (0.5 * word_count) + (0.3 * position_score) + (0.2 * density * 100)
        
        # Keep same threshold
        return relevance_score > 0.2
    
    async def _crawl_additional_pages(
        self,
        links: List[str],
        base_url: str,
        config: CrawlerConfig,
        include_images: bool = False,
        output_dir: Optional[Path] = None,
        topic: Optional[str] = None
    ) -> List[ExtractionResult]:
        """Crawl additional pages from the initial links."""
        results = []
        
        # Filter and prioritize links
        filtered_links = self._filter_links(links, base_url, config)
        
        # Limit to max_pages
        links_to_crawl = filtered_links[:config.max_pages - 1]  # -1 because we already crawled the initial page
        
        # Create tasks for each link
        tasks = []
        for link in links_to_crawl:
            task = self._extract_single_url(
                link,
                include_images=include_images,
                output_dir=output_dir,
                topic=topic
            )
            tasks.append(task)
        
        # Run all tasks concurrently with a limit
        batch_size = min(config.max_concurrent, len(tasks))
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            # Filter out exceptions and failed results
            for result in batch_results:
                if isinstance(result, ExtractionResult) and result.success:
                    results.append(result)
        
        return results
    
    def _filter_links(self, links: List[str], base_url: str, config: CrawlerConfig) -> List[str]:
        """Filter and prioritize links based on relevance."""
        filtered_links = []
        base_domain = urlparse(base_url).netloc
        
        # First pass: keep only links from the same domain
        same_domain_links = []
        for link in links:
            try:
                link_domain = urlparse(link).netloc
                if link_domain == base_domain:
                    same_domain_links.append(link)
            except Exception:
                continue
        
        # If we have a topic, prioritize links that mention the topic
        if config.topic:
            topic_lower = config.topic.lower()
            # Links that contain the topic in the URL
            topic_links = [link for link in same_domain_links 
                          if topic_lower in link.lower()]
            
            # Add topic links first, then the rest
            filtered_links.extend(topic_links)
            filtered_links.extend([link for link in same_domain_links 
                                 if link not in filtered_links])
        else:
            filtered_links = same_domain_links
        
        return filtered_links
    
    async def _enhance_with_llm(self, result: ExtractionResult, topic: Optional[str] = None):
        """Enhance extraction result with LLM processing using original prompt."""
        if not self.llm or not result.success or not result.data:
            return
        
        # Create a prompt using the exact formatting from original code
        topic_str = f"about '{topic}'" if topic else "from this web page"
        prompt = f"""
You are a data extraction system that ONLY outputs valid JSON. You never add explanatory text. You only output correctly formatted JSON data structures.

INSTRUCTIONS:
Extract structured data {topic_str} and return ONLY a valid JSON object.

OUTPUT FORMAT: 
You MUST follow these rules EXACTLY without exception:
1. Return ONLY a valid JSON object - no explanations, no intros, no markdown
2. Do NOT start with phrases like "Here's the JSON:", "Here's the data:", or "Certainly!"
3. Do NOT wrap the JSON in code fences (```)
4. Start your output with the opening brace {{
5. End your output with the closing brace }}
6. All JSON field names must be in double quotes
7. All string values must be in double quotes with proper escaping
8. Never explain your output or add notes before or after the JSON

JSON FIELDS TO INCLUDE:
- "title": {result.data.title}
- "description": A detailed summary (100-200 words) of what the article covers
- "main_content": The complete content of the article with proper markdown formatting

CONTENT EXTRACTION REQUIREMENTS:
1. Extract the COMPLETE article content, not just a summary
2. Include ALL code examples, tables, and technical specifications
3. Preserve ALL headings, subheadings and section structure
4. Include ALL relevant diagrams, charts, and visuals (described in markdown)
5. Capture the FULL technical depth and breadth of the content
6. Do not skip or summarize sections - extract EVERYTHING
7. Include ALL lists, bullet points, and enumerated items
8. Retain ALL technical terminology and jargon
9. Keep code samples exactly as they appear without simplification
10. Maintain tables with their full content and structure

When including code blocks in the main_content field, follow this exact format:
```language
code goes here
```
"""

        try:
            # Get enhancement from LLM
            response = await self.llm.generate_response(prompt)
            
            # Try to parse the JSON response
            import json
            import re
            
            # Extract JSON from the response - using your approach to handling various response formats
            json_match = re.search(r'```json\s*({.*?})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks - this pattern from your original code
                json_match = re.search(r'{[\s\S]*"main_content"[\s\S]*}', response)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    # Fallback to just trying the whole response
                    json_str = response.strip()
            
            # Clean up for JSON parsing
            json_str = json_str.strip()
            if not json_str.startswith('{'):
                json_str = '{' + json_str.split('{', 1)[1]
            if not json_str.endswith('}'):
                json_str = json_str.rsplit('}', 1)[0] + '}'
            
            enhanced = json.loads(json_str)
            
            # Update the extraction result
            if 'title' in enhanced and enhanced['title']:
                result.data.title = enhanced['title']
            
            if 'description' in enhanced and enhanced['description']:
                result.data.description = enhanced['description']
            
            if 'main_content' in enhanced and enhanced['main_content']:
                # Only replace if the enhanced content is substantial
                if len(enhanced['main_content']) > len(result.data.main_content) * 0.8:
                    result.data.main_content = enhanced['main_content']
                
        except Exception as e:
            self.logger.warning(f"Error enhancing with LLM: {str(e)}") 