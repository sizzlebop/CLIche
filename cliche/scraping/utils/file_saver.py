"""Utilities for saving scraped data to files."""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def save_scraped_data(
    data: Dict[str, Any], 
    url: str, 
    topic: Optional[str] = None
) -> Optional[str]:
    """
    Save scraped data to a JSON file in the correct location.
    
    Args:
        data: The scraped data to save (can be a Pydantic model or dict)
        url: The URL that was scraped
        topic: Optional topic for the file name
        
    Returns:
        Optional[str]: Path to the saved file or None if saving failed
    """
    try:
        # Create output directory
        home_dir = Path.home()
        output_dir = home_dir / "cliche" / "files" / "scrape"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unique filename
        domain = urlparse(url).netloc.replace('.', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if topic:
            # Sanitize topic for filename
            sanitized_topic = ''.join(c if c.isalnum() or c == '_' else '_' for c in topic)
            base_filename = f"scraped_{domain}_{sanitized_topic}"
        else:
            base_filename = f"scraped_{domain}"
            
        # Add timestamp for uniqueness    
        base_filename = f"{base_filename}_{timestamp}"
        
        # Save JSON file with custom encoder for datetime
        output_path = output_dir / f"{base_filename}.json"
        
        with open(output_path, "w") as f:
            # Handle different data types
            if hasattr(data, 'model_dump'):  # Pydantic v2
                json.dump(data.model_dump(), f, indent=2, cls=DateTimeEncoder)
            elif hasattr(data, 'dict'):  # Pydantic v1
                json.dump(data.dict(), f, indent=2, cls=DateTimeEncoder)
            else:
                # Assume it's already a dict
                json.dump(data, f, indent=2, cls=DateTimeEncoder)
        
        logger.info(f"Saved content to {output_path}")
        return str(output_path)
    
    except Exception as e:
        logger.error(f"Error saving scraped data: {str(e)}")
        return None 