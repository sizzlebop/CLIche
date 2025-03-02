"""
Image scraping utilities for CLIche.
Handles extracting and downloading images from web pages.
DEPRECATED: This module is maintained for backward compatibility.
Use cliche.scraping.extractors.image_extractor.ImageExtractor instead.
"""
import os
import re
import asyncio
import aiohttp
import hashlib
import warnings
import logging
import requests
from typing import List, Dict, Optional, Tuple, Set, Any, Union
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pydantic import BaseModel

# Import the ImageExtractor with relative imports to avoid circular dependencies
from ..scraping.extractors.image_extractor import ImageExtractor

# Configure logging
logger = logging.getLogger(__name__)

# Define ScrapedImage to maintain backward compatibility
class ScrapedImage(BaseModel):
    """Model for a scraped image."""
    url: str
    alt_text: str = ""
    caption: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    position_index: int = 0
    source_url: str = ""
    local_path: Optional[str] = None
    file_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'url': self.url,
            'alt': self.alt_text,
            'caption': self.caption,
            'width': self.width,
            'height': self.height,
            'position': self.position_index,
            'source': self.source_url,
            'local_path': self.local_path,
            'file_type': self.file_type
        }

# Make deprecation warnings more visible
warnings.filterwarnings("always", category=DeprecationWarning)

async def extract_images_async(
    html_content: str,
    base_url: str,
    max_images: int = 10,
    min_size: int = 100,
    include_metadata: bool = True
) -> List[ScrapedImage]:
    """
    Extract images from HTML content asynchronously.
    
    DEPRECATED: Use cliche.scraping.extractors.image_extractor.ImageExtractor instead.
    
    Args:
        html_content: HTML content to extract images from
        base_url: Base URL for resolving relative URLs
        max_images: Maximum number of images to extract
        min_size: Minimum width/height in pixels
        include_metadata: Whether to include metadata
        
    Returns:
        List of ScrapedImage objects
    """
    # Ensure the warning is displayed by using a module-level warning
    warnings.warn(
        "extract_images_async is deprecated. Use cliche.scraping.extractors.image_extractor.ImageExtractor instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    
    # Use new ImageExtractor
    extractor = ImageExtractor()
    images = await extractor.extract_images(
        html_content=html_content,
        base_url=base_url,
        max_images=max_images,
        min_size=min_size,
        output_dir=None  # Don't save images yet
    )
    
    # Convert to old format if needed
    if isinstance(images[0], Dict):
        return [ScrapedImage(**img) for img in images]
    return images

async def extract_and_download_images_async(
    html_content: str,
    base_url: str,
    max_images: int = 10,
    min_size: int = 100,
    output_dir: Optional[Path] = None,
    topic: Optional[str] = None
) -> List[ScrapedImage]:
    """
    Extract and download images from HTML content asynchronously.
    
    DEPRECATED: Use cliche.scraping.extractors.image_extractor.ImageExtractor instead.
    
    Args:
        html_content: HTML content to extract images from
        base_url: Base URL for resolving relative URLs
        max_images: Maximum number of images to extract
        min_size: Minimum width/height in pixels
        output_dir: Directory to save images to
        topic: Optional topic for organizing images
        
    Returns:
        List of ScrapedImage objects with local_path set
    """
    warnings.warn(
        "extract_and_download_images_async is deprecated. Use cliche.scraping.extractors.image_extractor.ImageExtractor instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    
    # Use new ImageExtractor
    extractor = ImageExtractor()
    images = await extractor.extract_images(
        html_content=html_content,
        base_url=base_url,
        max_images=max_images,
        min_size=min_size,
        output_dir=output_dir,
        topic=topic
    )
    
    # Convert to old format if needed
    if images and isinstance(images[0], Dict):
        return [ScrapedImage(**img) for img in images]
    return images

def extract_images(
    html_content: str,
    base_url: str,
    max_images: int = 10,
    min_size: int = 100,
    include_metadata: bool = True
) -> List[ScrapedImage]:
    """
    Extract images from HTML content (synchronous wrapper).
    
    DEPRECATED: Use cliche.scraping.extractors.image_extractor.ImageExtractor instead.
    
    Args:
        html_content: HTML content to extract images from
        base_url: Base URL for resolving relative URLs
        max_images: Maximum number of images to extract
        min_size: Minimum width/height in pixels
        include_metadata: Whether to include metadata
        
    Returns:
        List of ScrapedImage objects
    """
    warnings.warn(
        "extract_images is deprecated. Use cliche.scraping.extractors.image_extractor.ImageExtractor instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    
    # Run the async function in a new event loop
    return asyncio.run(extract_images_async(
        html_content=html_content,
        base_url=base_url,
        max_images=max_images,
        min_size=min_size,
        include_metadata=include_metadata
    ))

def extract_and_download_images(
    html_content: str,
    base_url: str,
    max_images: int = 10,
    min_size: int = 100,
    output_dir: Optional[Path] = None,
    topic: Optional[str] = None
) -> List[ScrapedImage]:
    """
    Extract and download images from HTML content (synchronous wrapper).
    
    DEPRECATED: Use cliche.scraping.extractors.image_extractor.ImageExtractor instead.
    
    Args:
        html_content: HTML content to extract images from
        base_url: Base URL for resolving relative URLs
        max_images: Maximum number of images to extract
        min_size: Minimum width/height in pixels
        output_dir: Directory to save images to
        topic: Optional topic for organizing images
        
    Returns:
        List of ScrapedImage objects with local_path set
    """
    warnings.warn(
        "extract_and_download_images is deprecated. Use cliche.scraping.extractors.image_extractor.ImageExtractor instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    
    # Run the async function in a new event loop
    return asyncio.run(extract_and_download_images_async(
        html_content=html_content,
        base_url=base_url,
        max_images=max_images,
        min_size=min_size,
        output_dir=output_dir,
        topic=topic
    ))

async def extract_images_from_html(html_content: str, base_url: str, 
                                   max_images: int = 10, 
                                   min_size: int = 100) -> List[ScrapedImage]:
    """Extract images from HTML content.
    
    Args:
        html_content: HTML content to extract images from
        base_url: Base URL of the page for resolving relative URLs
        max_images: Maximum number of images to extract
        min_size: Minimum width/height for images to extract
        
    Returns:
        List of ScrapedImage objects
    """
    soup = BeautifulSoup(html_content, 'lxml')
    
    images = []
    position_index = 0
    
    print(f"DEBUG: Looking for images in HTML from {base_url}")
    print(f"DEBUG: Found {len(soup.find_all('img'))} img tags in total")
    
    # Find all img tags
    for img_tag in soup.find_all('img'):
        # Skip if we've reached the maximum number of images
        if len(images) >= max_images:
            break
            
        # Skip tracking pixels, icons, etc.
        if 'width' in img_tag.attrs and int(img_tag.attrs['width']) < min_size:
            print(f"DEBUG: Skipping small image with width {img_tag.attrs['width']}")
            continue
        if 'height' in img_tag.attrs and int(img_tag.attrs['height']) < min_size:
            print(f"DEBUG: Skipping small image with height {img_tag.attrs['height']}")
            continue
            
        # Get image URL
        src = img_tag.get('src') or img_tag.get('data-src')
        if not src:
            print("DEBUG: Found img tag without src attribute")
            continue
            
        # Resolve relative URLs
        full_url = urljoin(base_url, src)
        print(f"DEBUG: Found image: {full_url}")
        
        # Get alt text and dimensions
        alt_text = img_tag.get('alt', '')
        width = int(img_tag.get('width', 0)) or None
        height = int(img_tag.get('height', 0)) or None
        
        # Try to find a caption (often in a nearby figcaption)
        caption = ""
        figure_parent = img_tag.find_parent('figure')
        if figure_parent:
            figcaption = figure_parent.find('figcaption')
            if figcaption:
                caption = figcaption.get_text(strip=True)
        
        # Create ScrapedImage object
        image = ScrapedImage(
            url=full_url,
            alt_text=alt_text,
            caption=caption,
            width=width,
            height=height,
            position_index=position_index,
            source_url=base_url
        )
        
        images.append(image)
        position_index += 1
    
    print(f"DEBUG: Successfully extracted {len(images)} images from HTML")
    return images


async def download_image(session: aiohttp.ClientSession, image: ScrapedImage, 
                         output_dir: Path) -> Optional[Path]:
    """Download an image and save it to the output directory.
    
    Args:
        session: aiohttp ClientSession for HTTP requests
        image: ScrapedImage object to download
        output_dir: Directory to save the image to
        
    Returns:
        Path to the downloaded image file, or None if download failed
    """
    try:
        # Make output directory if it doesn't exist
        print(f"DEBUG: Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a consistent filename
        filename = image.get_filename()
        output_path = output_dir / filename
        
        # Skip if already downloaded
        if output_path.exists():
            print(f"DEBUG: Image already exists at {output_path}, skipping download")
            image.local_path = output_path
            return output_path
        
        # Download the image
        print(f"DEBUG: Downloading image from {image.url}")
        async with session.get(image.url, timeout=30) as response:
            if response.status != 200:
                print(f"DEBUG: Failed to download image, status code: {response.status}")
                return None
                
            # Determine file type from Content-Type header
            content_type = response.headers.get('Content-Type', '')
            print(f"DEBUG: Image content type: {content_type}")
            if 'image/' in content_type:
                image.file_type = content_type.split('/')[-1].split(';')[0]  # e.g., image/jpeg -> jpeg
                
                # Update filename if we now know the file type
                if image.file_type:
                    filename = image.get_filename()
                    output_path = output_dir / filename
            
            # Save the image
            print(f"DEBUG: Saving image to {output_path}")
            with open(output_path, 'wb') as f:
                f.write(await response.read())
            
            print(f"DEBUG: Successfully saved image to {output_path}")    
            image.local_path = output_path
            return output_path
            
    except Exception as e:
        print(f"DEBUG: Error downloading image {image.url}: {str(e)}")
        return None


async def download_images_async(images: List[ScrapedImage], output_dir: Optional[Path] = None) -> List[ScrapedImage]:
    """Download multiple images asynchronously.
    
    Args:
        images: List of ScrapedImage objects to download
        output_dir: Directory to save images to (defaults to ~/cliche/files/images/scraped)
        
    Returns:
        List of ScrapedImage objects with updated local_path
    """
    # Default to ~/cliche/files/images/scraped
    if not output_dir:
        output_dir = get_image_dir() / "scraped"
        print(f"DEBUG: Using default output directory: {output_dir}")
    else:
        print(f"DEBUG: Using provided output directory: {output_dir}")
        
    # Make directory if it doesn't exist
    print(f"DEBUG: Creating output directory structure: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use aiohttp for async downloads
    print(f"DEBUG: Starting download of {len(images)} images")
    async with aiohttp.ClientSession() as session:
        tasks = [download_image(session, image, output_dir) for image in images]
        await asyncio.gather(*tasks)
        
    # Return only images that were successfully downloaded
    downloaded = [img for img in images if img.local_path]
    print(f"DEBUG: Successfully downloaded {len(downloaded)} out of {len(images)} images")
    return downloaded


async def extract_and_download_images_async(html_content: str, base_url: str, 
                                   max_images: int = 10, min_size: int = 100,
                                   output_dir: Optional[Path] = None, 
                                   topic: Optional[str] = None) -> List[ScrapedImage]:
    """Async version of extract_and_download_images for use within an async context.
    
    Args:
        html_content: HTML content to extract images from
        base_url: Base URL of the page for resolving relative URLs
        max_images: Maximum number of images to extract
        min_size: Minimum width/height for images to extract
        output_dir: Directory to save images to (defaults to ~/cliche/files/images/scraped)
        topic: Optional topic name for creating a topic-specific subfolder
        
    Returns:
        List of ScrapedImage objects with local_path set
    """
    print(f"DEBUG: Starting async image extraction from {base_url}")
    
    # Create a well-named subfolder for this scrape session
    if not output_dir:
        base_output_dir = get_image_dir() / "scraped"
        
        # Get domain for folder naming
        domain = urlparse(base_url).netloc
        domain = re.sub(r'[^\w\-]', '_', domain.lower())
        
        # Create a folder name that matches the JSON file pattern
        if topic:
            subfolder = f"scraped_{domain}_{topic}"
        else:
            subfolder = f"scraped_{domain}"
        
        # Add timestamp to ensure uniqueness
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        subfolder = f"{subfolder}_{timestamp}"
        
        output_dir = base_output_dir / subfolder
        print(f"DEBUG: Created organized subfolder for images: {output_dir}")
    else:
        print(f"DEBUG: Using provided output directory: {output_dir}")
    
    # Ensure the directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract images
    images = await extract_images_from_html(html_content, base_url, max_images, min_size)
    
    # Download images to the organized subfolder
    if images:
        print(f"DEBUG: Found {len(images)} images, starting download to {output_dir}")
        downloaded_images = await download_images_async(images, output_dir)
        return downloaded_images
    else:
        print(f"DEBUG: No images found in content from {base_url}")
    
    return []
    
def extract_and_download_images(html_content: str, base_url: str, 
                               max_images: int = 10, min_size: int = 100,
                               output_dir: Optional[Path] = None,
                               topic: Optional[str] = None) -> List[ScrapedImage]:
    """Extract and download images from HTML content.
    
    This is a synchronous wrapper for the async version.
    Do not use this from inside an async function - use extract_and_download_images_async instead.
    
    Args:
        html_content: HTML content to extract images from
        base_url: Base URL of the page for resolving relative URLs
        max_images: Maximum number of images to extract
        min_size: Minimum width/height for images to extract
        output_dir: Directory to save images to (defaults to ~/cliche/files/images/scraped)
        topic: Optional topic name for creating a topic-specific subfolder
        
    Returns:
        List of ScrapedImage objects with local_path set
    """
    print(f"DEBUG: Starting image extraction from {base_url}")
    
    # Create a well-named subfolder for this scrape session
    if not output_dir:
        base_output_dir = get_image_dir() / "scraped"
        
        # Get domain for folder naming
        domain = urlparse(base_url).netloc
        domain = re.sub(r'[^\w\-]', '_', domain.lower())
        
        # Create a folder name that matches the JSON file pattern
        if topic:
            subfolder = f"scraped_{domain}_{topic}"
        else:
            subfolder = f"scraped_{domain}"
        
        # Add timestamp to ensure uniqueness
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        subfolder = f"{subfolder}_{timestamp}"
        
        output_dir = base_output_dir / subfolder
        print(f"DEBUG: Created organized subfolder for images: {output_dir}")
    else:
        print(f"DEBUG: Using provided output directory: {output_dir}")
    
    # Ensure the directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # We need to manually extract and process images
    print(f"DEBUG: Using synchronous image extraction")
    soup = BeautifulSoup(html_content, 'lxml')
    
    extracted_images = []
    position_index = 0
    
    print(f"DEBUG: Found {len(soup.find_all('img'))} img tags in total")
    
    # Find all img tags
    for img_tag in soup.find_all('img'):
        # Skip if we've reached the maximum number of images
        if len(extracted_images) >= max_images:
            break
            
        # Skip tracking pixels, icons, etc.
        if 'width' in img_tag.attrs and int(img_tag.attrs['width']) < min_size:
            print(f"DEBUG: Skipping small image with width {img_tag.attrs['width']}")
            continue
        if 'height' in img_tag.attrs and int(img_tag.attrs['height']) < min_size:
            print(f"DEBUG: Skipping small image with height {img_tag.attrs['height']}")
            continue
            
        # Get image URL
        src = img_tag.get('src') or img_tag.get('data-src')
        if not src:
            print("DEBUG: Found img tag without src attribute")
            continue
            
        # Resolve relative URLs
        if src.startswith('//'):
            src = 'https:' + src
        elif not src.startswith('http'):
            src = urljoin(base_url, src)
            
        print(f"DEBUG: Found image: {src}")
        
        # Generate a consistent filename
        parsed_url = urlparse(src)
        filename = os.path.basename(parsed_url.path)
        if not re.match(r'.*\.(jpg|jpeg|png|gif|webp|svg)$', filename, re.IGNORECASE):
            url_hash = hashlib.md5(src.encode()).hexdigest()[:10]
            filename = f"scraped_image_{url_hash}.jpg"
        
        output_path = output_dir / filename
        
        # Skip if already downloaded
        if output_path.exists():
            print(f"DEBUG: Image already exists at {output_path}, skipping download")
            
            # Add to extracted images list
            extracted_images.append(ScrapedImage(
                url=src,
                alt_text=img_tag.get('alt', ''),
                caption="",
                width=int(img_tag.get('width', 0)) if img_tag.get('width') else None,
                height=int(img_tag.get('height', 0)) if img_tag.get('height') else None,
                position_index=position_index,
                source_url=base_url
            ))
            extracted_images[-1].local_path = output_path
            position_index += 1
            continue
        
        # Download the image
        try:
            print(f"DEBUG: Downloading image from {src}")
            response = requests.get(src, timeout=30)
            
            if response.status_code != 200:
                print(f"DEBUG: Failed to download image, status code: {response.status_code}")
                continue
                
            # Determine file type from Content-Type header
            content_type = response.headers.get('Content-Type', '')
            file_type = None
            
            if 'image/' in content_type:
                file_type = content_type.split('/')[-1].split(';')[0]  # e.g., image/jpeg -> jpeg
                
                # Update filename if we now know the file type
                if file_type:
                    filename = f"scraped_image_{url_hash}.{file_type}"
                    output_path = output_dir / filename
            
            # Save the image
            print(f"DEBUG: Saving image to {output_path}")
            with open(output_path, 'wb') as f:
                f.write(response.content)
                
            # Create and add ScrapedImage object
            image = ScrapedImage(
                url=src,
                alt_text=img_tag.get('alt', ''),
                caption="",
                width=int(img_tag.get('width', 0)) if img_tag.get('width') else None,
                height=int(img_tag.get('height', 0)) if img_tag.get('height') else None,
                position_index=position_index,
                source_url=base_url
            )
            image.local_path = output_path
            image.file_type = file_type
            
            extracted_images.append(image)
            position_index += 1
            print(f"DEBUG: Successfully saved image to {output_path}")
            
        except Exception as e:
            print(f"DEBUG: Error downloading image {src}: {str(e)}")
    
    print(f"DEBUG: Extracted {len(extracted_images)} images")
    return extracted_images 