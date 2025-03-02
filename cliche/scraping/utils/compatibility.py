"""Compatibility utilities for integrating existing code."""
from typing import List, Dict, Any
from ..models.data_models import ScrapedImage

def convert_scraped_images(original_images: List[Any]) -> List[Dict[str, Any]]:
    """Convert images from the original image scraper format to our ScrapedImage format.
    
    Args:
        original_images: Images from the original image scraper
        
    Returns:
        List of image dictionaries compatible with our ScrapedData model
    """
    converted_images = []
    
    for img in original_images:
        # If the image is already a dict, use it directly
        if isinstance(img, dict):
            converted_images.append(img)
            continue
            
        # If the image has a to_dict method, use it
        if hasattr(img, 'to_dict'):
            converted_images.append(img.to_dict())
            continue
            
        # Otherwise, create a compatible dict
        # Adjust the field names as needed based on your actual image scraper
        converted_image = {
            'url': getattr(img, 'url', ''),
            'alt': getattr(img, 'alt_text', ''),
            'width': getattr(img, 'width', 0),
            'height': getattr(img, 'height', 0),
            'local_path': getattr(img, 'local_path', '')
        }
        
        converted_images.append(converted_image)
    
    return converted_images 