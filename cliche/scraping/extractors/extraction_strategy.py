"""Custom extraction strategy for crawl4ai that works with all providers."""
import os
import json
import logging
from typing import Optional, Dict, Any
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from ...core import CLIche

class ProviderExtractionStrategy(LLMExtractionStrategy):
    """Extraction strategy that works with all supported LLM providers."""

    def __init__(self, llm_client=None):
        """Initialize the extraction strategy."""
        super().__init__(llm_client)
        self.logger = logging.getLogger(__name__)

        if not llm_client:
            try:
                cliche = CLIche()
                self.llm_client = cliche.provider
                self.logger.info(f"Using provider: {cliche.config.config.get('provider')}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize LLM provider: {str(e)}")
                self.llm_client = None

    async def extract(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Extract structured content using the configured provider.

        Args:
            html: The HTML content to extract from
            url: The source URL

        Returns:
            Optional[Dict[str, Any]]: Extracted content or None if extraction fails
        """
        if not self.llm_client:
            self.logger.warning("No LLM provider available")
            return None

        try:
            # Create extraction prompt
            prompt = self._create_extraction_prompt(html, url)
            
            # Get response from provider
            response = await self.llm_client.generate_response(prompt)
            
            # Parse response based on provider format
            if isinstance(response, dict):
                # Some providers return structured data directly
                return response
            else:
                # Try to parse text response as JSON
                text = str(response).strip()
                try:
                    # Find JSON content between curly braces
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = text[start:end]
                        return json.loads(json_str)
                    else:
                        self.logger.warning("No valid JSON found in response")
                        return None
                except Exception as e:
                    self.logger.error(f"Failed to parse LLM response: {str(e)}")
                    return None

        except Exception as e:
            self.logger.error(f"Extraction error: {str(e)}")
            return None

    def _create_extraction_prompt(self, html: str, url: str) -> str:
        """Create a prompt for content extraction.
        
        Args:
            html: The HTML content to extract from
            url: The source URL

        Returns:
            str: The formatted prompt
        """
        return f"""Extract structured data from this webpage and return it as JSON.

URL: {url}

OUTPUT FORMAT:
{{
    "title": "The page title",
    "description": "A detailed summary (100-200 words)",
    "main_content": "The complete content in markdown",
    "metadata": {{
        "author": "Page author if available",
        "date": "Publication date if available",
        "type": "Content type (article, documentation, etc.)",
        "topics": ["Relevant topics"]
    }}
}}

REQUIREMENTS:
1. Extract ALL content completely
2. Format content as proper markdown
3. Preserve code blocks with language tags
4. Keep all lists and tables
5. Maintain section structure

CONTENT TO PROCESS:
{html[:20000]}  # Limit content length for LLM
"""