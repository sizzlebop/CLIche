"""
Unsplash API utilities for CLIche.
Handles searching, downloading, and managing images from Unsplash.
"""
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import click
from .file import get_output_dir

class UnsplashAPI:
    """Wrapper for the Unsplash API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Unsplash API client.
        
        Args:
            api_key: Optional API key. If not provided, will try to get from environment.
        """
        # First try the provided API key
        self.api_key = api_key
        
        # If not provided, try to get from environment
        if not self.api_key:
            self.api_key = os.getenv('UNSPLASH_API_KEY')
        
        # If still not found, check the config file directly
        if not self.api_key:
            try:
                from ..core import Config
                config = Config()
                if 'services' in config.config and 'unsplash' in config.config['services']:
                    self.api_key = config.config['services']['unsplash'].get('api_key')
                # Also check in providers section as a fallback if it exists there
                elif 'providers' in config.config and 'unsplash' in config.config['providers']:
                    self.api_key = config.config['providers']['unsplash'].get('api_key')
            except Exception as e:
                # If there's any error loading the config, just continue
                pass
        
        # If API key is still not found, raise an error
        if not self.api_key:
            raise ValueError("Unsplash API key not found. Please configure it with 'cliche config --unsplash-key YOUR_API_KEY'")
        
        self.api_base = "https://api.unsplash.com"
        self.headers = {
            "Authorization": f"Client-ID {self.api_key}",
            "Accept-Version": "v1"
        }
        
        # Create image directory if it doesn't exist
        self.image_dir = get_image_dir()
        
    def search_photos(self, query: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Search for photos on Unsplash.
        
        Args:
            query: Search query
            page: Page number
            per_page: Number of results per page
            
        Returns:
            Dictionary with search results
        """
        url = f"{self.api_base}/search/photos"
        params = {
            "query": query,
            "page": page,
            "per_page": per_page
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_photo(self, photo_id: str) -> Dict[str, Any]:
        """Get a specific photo by ID.
        
        Args:
            photo_id: The Unsplash photo ID
            
        Returns:
            Dictionary with photo details
        """
        url = f"{self.api_base}/photos/{photo_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def download_photo(self, photo_id: str, width: int = 1600, height: int = 900, 
                       filename: Optional[str] = None) -> Path:
        """Download a photo from Unsplash.
        
        Args:
            photo_id: The Unsplash photo ID
            width: Desired width
            height: Desired height
            filename: Optional custom filename
            
        Returns:
            Path to the downloaded image file
        """
        # Get photo details
        photo = self.get_photo(photo_id)
        
        # Track download
        self._track_download(photo_id)
        
        # Get download URL
        download_url = photo["urls"]["raw"] + f"&w={width}&h={height}&fit=crop"
        
        # Determine filename
        if not filename:
            # Use photo ID + photographer username for a unique filename
            photographer = photo["user"]["username"]
            filename = f"{photo_id}_{photographer}.jpg"
        
        # Create output path
        output_path = self.image_dir / filename
        
        # Download the image
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return output_path
    
    def _track_download(self, photo_id: str) -> None:
        """Track a download (required by Unsplash API terms).
        
        Args:
            photo_id: The Unsplash photo ID
        """
        url = f"{self.api_base}/photos/{photo_id}/download"
        try:
            requests.get(url, headers=self.headers)
        except Exception:
            # Don't fail if tracking fails
            pass
            
    def get_photo_url(self, photo_id: str, width: int = 1600, height: int = 900) -> dict:
        """Get a photo URL and metadata without downloading.
        
        Args:
            photo_id: The Unsplash photo ID
            width: Desired width
            height: Desired height
            
        Returns:
            Dictionary with photo URL and metadata
        """
        # Get photo details
        photo = self.get_photo(photo_id)
        
        # Track download (required by Unsplash API terms)
        self._track_download(photo_id)
        
        # Get direct URLs
        url = photo["urls"]["regular"]  # Use the "regular" sized image (1080px)
        
        # If specific dimensions requested, use the raw URL with dimensions
        if width or height:
            url = photo["urls"]["raw"] + f"&w={width}&h={height}&fit=crop"
        
        # Get photographer info
        photographer_name = photo["user"]["name"]
        photographer_username = photo["user"]["username"]
        photographer_url = f"https://unsplash.com/@{photographer_username}?utm_source=cliche&utm_medium=referral"
        
        # Return URL and metadata
        return {
            "url": url,
            "alt_text": photo.get("description") or photo.get("alt_description") or "Image from Unsplash",
            "photographer_name": photographer_name,
            "photographer_username": photographer_username,
            "photographer_url": photographer_url,
            "unsplash_url": "https://unsplash.com/?utm_source=cliche&utm_medium=referral"
        }


def get_image_dir() -> Path:
    """Get the directory for storing downloaded images."""
    # Get user's home directory
    home = Path.home()
    
    # Create base cliche directory if it doesn't exist (removing the dot to make it visible)
    cliche_dir = home / 'cliche'
    cliche_dir.mkdir(exist_ok=True)
    
    # Create files directory if it doesn't exist
    files_dir = cliche_dir / 'files'
    files_dir.mkdir(exist_ok=True)
    
    # Create images directory if it doesn't exist
    images_dir = files_dir / 'images'
    images_dir.mkdir(exist_ok=True)
    
    return images_dir


def is_absolute_path(path):
    """
    Check if a path is absolute.
    
    Args:
        path: Path to check
        
    Returns:
        Boolean indicating if the path is absolute
    """
    return os.path.isabs(path)


def format_image_for_markdown(image_path: str, alt_text: str = "", width: int = None) -> str:
    """
    Format an image for inclusion in markdown documents.

    Args:
        image_path: Path or URL to the image
        alt_text: Alternative text for the image
        width: Optional width for the image

    Returns:
        Formatted markdown image
    """
    # If it's already a URL, use it directly
    if image_path.startswith("http"):
        # For markdown, we'll use standard syntax without width (more compatible)
        return f"![{alt_text}]({image_path})"
    else:
        # Convert to absolute path
        if not is_absolute_path(image_path):
            image_path = os.path.abspath(image_path)

        # For local files, we'll still include the width attribute for renderers that support it
        if width:
            return f"![{alt_text}]({image_path}) {{width={width}px}}"
        else:
            return f"![{alt_text}]({image_path})"


def format_image_for_html(image_path: str, alt_text: str = "", width: int = None, 
                        css_class: str = "unsplash-image") -> str:
    """Format an image for inclusion in HTML documents.
    
    Args:
        image_path: Path or URL to the image
        alt_text: Alternative text for the image
        width: Optional width specification
        css_class: CSS class to apply to the image
        
    Returns:
        HTML image tag
    """
    # If it's already a URL, use it directly
    if image_path.startswith("http"):
        style = f"width: {width}px;" if width else ""
        return f'<img src="{image_path}" alt="{alt_text}" class="{css_class}" style="{style}">'
    else:
        # Convert to absolute path
        abs_path = Path(image_path).resolve()
        
        # Create HTML image tag
        style = f"width: {width}px;" if width else ""
        return f'<img src="{abs_path}" alt="{alt_text}" class="{css_class}" style="{style}">'


def get_photo_credit(photo_data: Dict[str, Any], format: str = "markdown") -> str:
    """Generate photo credit text as required by Unsplash API terms.
    
    Args:
        photo_data: Photo data from Unsplash API
        format: Output format ('markdown' or 'html')
        
    Returns:
        Formatted credit text
    """
    photographer = photo_data["user"]["name"]
    username = photo_data["user"]["username"]
    unsplash_link = f"https://unsplash.com/@{username}?utm_source=cliche&utm_medium=referral"
    
    if format.lower() == "markdown":
        return f"Photo by [{photographer}]({unsplash_link}) on [Unsplash](https://unsplash.com/?utm_source=cliche&utm_medium=referral)"
    elif format.lower() == "html":
        return f'Photo by <a href="{unsplash_link}" target="_blank">{photographer}</a> on <a href="https://unsplash.com/?utm_source=cliche&utm_medium=referral" target="_blank">Unsplash</a>'
    else:
        return f"Photo by {photographer} on Unsplash" 