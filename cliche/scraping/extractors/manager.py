"""Manager for coordinating different content extractors."""
import logging
from typing import List, Optional, Dict, Any, Tuple, Union
from urllib.parse import urlparse
import os
import importlib

# Import the BaseExtractor class
from .base_extractor import BaseExtractor
from .general_extractor import GeneralExtractor
from .wikipedia_extractor import WikipediaExtractor
from .python_docs_extractor import PythonDocsExtractor
from ..models.data_models import ExtractionResult, ScrapedData

class ExtractorManager:
    """Manages multiple specialized content extractors."""
    
    def __init__(self):
        """Initialize the extractor manager."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize extractors
        self._extractors = [
            WikipediaExtractor(),
            PythonDocsExtractor(),
            GeneralExtractor()  # This should be last as the fallback
        ]
        
        # Initialize CLIche for provider access - improved error handling
        self.llm = None
        try:
            # Import at runtime to avoid circular imports
            module_name = "cliche.core"
            module = importlib.import_module(module_name)
            
            if hasattr(module, 'CLIche'):
                cliche_class = getattr(module, 'CLIche')
                cliche_instance = cliche_class()
                
                # If the instance has a provider attribute, use it
                if hasattr(cliche_instance, 'provider'):
                    self.llm = cliche_instance.provider
                    
                    # Get provider name for logging
                    if hasattr(cliche_instance, 'config') and hasattr(cliche_instance.config, 'config'):
                        provider_name = cliche_instance.config.config.get("provider", "unknown")
                        self.logger.info(f"Using LLM provider: {provider_name}")
                    else:
                        self.logger.info("Using LLM provider (name unknown)")
            else:
                self.logger.warning("CLIche class not found in core module")
                
        except ImportError:
            self.logger.warning("Could not import cliche.core module")
        except Exception as e:
            self.logger.warning(f"Failed to initialize LLM provider: {str(e)}")
    
    def get_extractor_for_url(self, url: str) -> BaseExtractor:
        """Get the appropriate extractor for a URL, matching original functionality."""
        from urllib.parse import urlparse
        
        parsed_url = urlparse(url)
        
        # Wikipedia detection (from original code)
        if "wikipedia.org" in url.lower():
            return self.get_extractor("wikipedia")
        
        # Python.org detection (from original code)
        if parsed_url.netloc.lower() in ["python.org", "www.python.org", "docs.python.org"]:
            return self.get_extractor("python_docs")
        
        # Add any other specialized domains from your original code
        
        # Default to general extractor
        return self.get_extractor("general")
    
    async def extract(self, url: str, topic: Optional[str] = None,
                    include_images: bool = False, max_images: int = 10,
                    min_image_size: int = 100, image_dir: Optional[str] = None,
                    use_llm: bool = True) -> ExtractionResult:
        """
        Extract content from a URL using the most appropriate extractor.
        
        Args:
            url: The URL to extract content from
            topic: Optional topic to focus on
            include_images: Whether to extract images
            max_images: Maximum number of images to extract
            min_image_size: Minimum size for images to extract
            image_dir: Optional directory to save images to
            use_llm: Whether to use LLM enhancement
            
        Returns:
            ExtractionResult with scraped data or error
        """
        try:
            # Set LLM usage flag in environment
            if not use_llm:
                os.environ["CLICHE_NO_LLM"] = "1"
            elif "CLICHE_NO_LLM" in os.environ:
                del os.environ["CLICHE_NO_LLM"]
                
            # Get the appropriate extractor
            extractor = self.get_extractor_for_url(url)
            
            # Pass LLM instance if needed and available
            if use_llm and self.llm and hasattr(extractor, 'llm'):
                extractor.llm = self.llm
            
            # Perform extraction
            result = await extractor.extract(
                url=url,
                topic=topic,
                include_images=include_images,
                max_images=max_images,
                min_image_size=min_image_size,
                image_dir=image_dir
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error in extraction: {str(e)}")
            return ExtractionResult(
                success=False,
                error=f"Extraction failed: {str(e)}"
            )
    
    def cleanup(self):
        """Clean up resources used by extractors."""
        for extractor in self._extractors:
            if hasattr(extractor, 'cleanup'):
                try:
                    extractor.cleanup()
                except Exception as e:
                    self.logger.warning(f"Error cleaning up {extractor.__class__.__name__}: {e}")

    def get_extractor(self, extractor_type: str) -> BaseExtractor:
        """Get an extractor by type name."""
        extractor_map = {
            "wikipedia": self._extractors[0],  # WikipediaExtractor
            "python_docs": self._extractors[1],  # PythonDocsExtractor
            "general": self._extractors[2]  # GeneralExtractor
        }
        
        return extractor_map.get(extractor_type.lower(), self._extractors[2])  # Default to general

def get_extractor_manager() -> ExtractorManager:
    """Get a configured extractor manager instance."""
    return ExtractorManager()