"""Image extraction functionality for CLIche."""
import os
import re
import logging
import aiohttp
import hashlib
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime

from ..models.data_models import ScrapedImage
from ..utils.html_processing import is_element_node, has_attribute

class ImageExtractor:
    """Extracts and processes images from web content."""

    def __init__(self):
        """Initialize the image extractor."""
        self.logger = logging.getLogger(__name__)

    async def extract_images(
        self,
        html_content: str,
        base_url: str,
        max_images: int = 10,
        min_size: int = 100,
        output_dir: Optional[Path] = None,
        topic: Optional[str] = None
    ) -> List[ScrapedImage]:
        """
        Extract images from HTML content.
        
        Args:
            html_content: HTML content to extract images from
            base_url: Base URL for resolving relative URLs
            max_images: Maximum number of images to extract
            min_size: Minimum width/height in pixels
            output_dir: Directory to save images to
            topic: Optional topic for organizing images
            
        Returns:
            List of ScrapedImage objects
        """
        try:
            self.logger.info(f"Extracting images from {base_url}")
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Find all image elements
            images = []
            position_index = 0
            
            for img in soup.find_all('img'):
                # Skip if we've reached the maximum
                if len(images) >= max_images:
                    break
                    
                # Get image URL
                src = img.get('src') or img.get('data-src')
                if not src:
                    continue
                    
                # Resolve relative URLs
                if src.startswith('//'):
                    src = f'https:{src}'
                elif not src.startswith(('http://', 'https://')):
                    # Use urljoin for proper URL resolution
                    src = urljoin(base_url, src)
                    
                # Get dimensions
                width = height = None
                if 'width' in img.attrs:
                    try:
                        width = int(img.attrs['width'])
                    except (ValueError, TypeError):
                        pass
                if 'height' in img.attrs:
                    try:
                        height = int(img.attrs['height'])
                    except (ValueError, TypeError):
                        pass
                        
                # Skip small images
                if width and height:
                    if width < min_size and height < min_size:
                        continue
                elif min_size > 0:
                    # Skip images without dimensions when size filtering is enabled
                    self.logger.debug(f"Skipping image without dimensions: {src}")
                    continue
                        
                # Get alt text and caption
                alt_text = img.get('alt', '')
                caption = self._extract_caption(img)
                
                # Create image object
                image = ScrapedImage(
                    url=src,
                    alt_text=alt_text,
                    caption=caption,
                    width=width,
                    height=height,
                    position_index=position_index,
                    source_url=base_url
                )
                
                images.append(image)
                position_index += 1
            
            # Download images if output directory specified
            if output_dir and images:
                downloaded_images = await self._download_images(images, output_dir, topic)
                return downloaded_images
            
            return images
            
        except Exception as e:
            self.logger.error(f"Error extracting images: {str(e)}")
            return []

    def _extract_caption(self, img_tag) -> str:
        """Extract caption from image context."""
        caption = ""
        
        # Check for figcaption
        figure_parent = img_tag.find_parent('figure')
        if figure_parent:
            figcaption = figure_parent.find('figcaption')
            if figcaption:
                caption = figcaption.get_text(strip=True)
                
        # Check for aria-label
        if not caption:
            caption = img_tag.get('aria-label', '')
            
        # Check for title attribute
        if not caption:
            caption = img_tag.get('title', '')
            
        return caption

    async def _download_images(
        self,
        images: List[ScrapedImage],
        output_dir: Path,
        topic: Optional[str] = None
    ) -> List[ScrapedImage]:
        """Download images to the specified directory."""
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        async def download_single_image(image: ScrapedImage) -> Optional[ScrapedImage]:
            try:
                # Generate filename using a hash of the URL
                url_hash = hashlib.md5(image.url.encode()).hexdigest()[:10]
                parsed_url = urlparse(image.url)
                original_filename = os.path.basename(parsed_url.path)
                
                # Determine extension
                if re.match(r'.*\.(jpg|jpeg|png|gif|webp|svg)$', original_filename, re.IGNORECASE):
                    ext = os.path.splitext(original_filename)[1]
                else:
                    ext = '.jpg'  # Default to jpg
                    
                filename = f"image_{url_hash}{ext}"
                output_path = output_dir / filename
                
                # Download the image
                async with aiohttp.ClientSession() as session:
                    async with await session.get(image.url, timeout=30) as response:
                        if response.status == 200:
                            # Get content type
                            content_type = response.headers.get('Content-Type', '')
                            if 'image/' in content_type:
                                image.file_type = content_type.split('/')[-1].split(';')[0]
                            
                            # Save the image
                            data = await response.read()
                            with open(output_path, 'wb') as f:
                                f.write(data)
                                
                            image.local_path = str(output_path)
                            return image
                            
                        self.logger.warning(f"Failed to download image: HTTP {response.status}")
                        return None
                        
            except Exception as e:
                self.logger.error(f"Error downloading image {image.url}: {str(e)}")
                return None
                
        # Download all images concurrently
        tasks = [download_single_image(img) for img in images]
        downloaded = await asyncio.gather(*tasks)
        
        # Filter out failed downloads
        return [img for img in downloaded if img is not None]

    def _fix_image_urls(self, html_content: str, base_url: str) -> str:
        """Fix relative image URLs in the HTML, like in the original implementation."""
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        
        soup = BeautifulSoup(html_content, 'lxml')
        for tag in soup.find_all(['a', 'img']):
            # Convert relative URLs to absolute
            if 'href' in tag.attrs:
                tag['href'] = urljoin(base_url, tag['href'])
            if 'src' in tag.attrs:
                tag['src'] = urljoin(base_url, tag['src'])
        
        return str(soup) 