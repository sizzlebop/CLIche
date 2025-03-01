"""
Utility functions and classes
"""
from .gpu import get_gpu_info
from .docker import get_docker_containers
from .generate_from_scrape import generate
from .unsplash import UnsplashAPI, format_image_for_markdown, format_image_for_html, get_photo_credit

# Import image generation modules
try:
    from .image_generation import ImageGenerator, ImageProvider
    from .dalle import DALLEGenerator
    from .stability import StabilityGenerator
    __image_generation_available = True
except ImportError:
    __image_generation_available = False

# Import image scraping modules
try:
    from .image_scraper import extract_and_download_images, ScrapedImage
    __image_scraper_available = True
except ImportError:
    __image_scraper_available = False

__all__ = [
    'get_gpu_info', 
    'get_docker_containers', 
    'generate',
    'UnsplashAPI',
    'format_image_for_markdown',
    'format_image_for_html',
    'get_photo_credit'
]

# Add image generation modules if available
if __image_generation_available:
    __all__.extend([
        'ImageGenerator',
        'ImageProvider',
        'DALLEGenerator',
        'StabilityGenerator'
    ])

# Add image scraper modules if available
if __image_scraper_available:
    __all__.extend([
        'extract_and_download_images',
        'ScrapedImage'
    ])
