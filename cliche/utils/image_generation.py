"""
Image generation utilities for CLIche.
Provides a unified interface for various image generation providers.
"""
import os
import json
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import click
from .file import get_output_dir, get_image_dir

class ImageProvider(str, Enum):
    """Supported image generation providers."""
    DALLE = "dalle"
    STABILITY = "stability"

class ImageGenerator:
    """Unified interface for image generation."""
    
    def __init__(self, provider: Optional[str] = None):
        """Initialize the image generator.
        
        Args:
            provider: Provider to use (dalle, stability). If not provided, uses default.
        """
        # Load configuration
        from ..core import Config
        self.config = Config().config
        
        # Use provided provider or default from config
        self.provider_name = provider or self.config.get('image_generation', {}).get('default_provider', 'dalle')
        
        # Get the actual provider instance
        self.provider = self._get_provider()
        
        # Image directory
        self.image_dir = get_image_dir()
    
    def _get_provider(self):
        """Get the provider instance based on selected provider name."""
        if self.provider_name.lower() == 'dalle':
            from .dalle import DALLEGenerator
            try:
                return DALLEGenerator()
            except Exception as e:
                raise Exception(f"Failed to initialize DALL-E: {str(e)}")
        elif self.provider_name.lower() == 'stability':
            from .stability import StabilityGenerator
            try:
                return StabilityGenerator()
            except Exception as e:
                raise Exception(f"Failed to initialize Stability AI: {str(e)}")
        else:
            raise ValueError(f"Unsupported provider: {self.provider_name}")
    
    def list_providers(self) -> List[Dict[str, str]]:
        """List available image generation providers.
        
        Returns:
            List of available providers with name and description
        """
        return [
            {
                "id": "dalle",
                "name": "DALL-E (OpenAI)",
                "description": "High-quality image generation from OpenAI"
            },
            {
                "id": "stability",
                "name": "Stability AI",
                "description": "Powerful open source image generation models"
            }
        ]
    
    def list_models(self, provider: Optional[str] = None) -> List[Dict[str, str]]:
        """List available models for a provider.
        
        Args:
            provider: Optional provider to list models for. If not provided, uses current.
            
        Returns:
            List of available models with name and description
        """
        if provider and provider != self.provider_name:
            # Create a temporary instance for the specified provider
            temp = ImageGenerator(provider)
            return temp.provider.list_models()
        
        # Use current provider
        return self.provider.list_models()
    
    def get_default_model(self, provider: Optional[str] = None) -> Optional[str]:
        """Get the default model for a provider from config.
        
        Args:
            provider: Provider to get default model for. If None, uses current.
            
        Returns:
            Default model name or None if not set
        """
        provider = provider or self.provider_name
        
        # Define provider-specific fallback defaults
        provider_defaults = {
            'dalle': 'dall-e-3',
            'stability': 'stable-diffusion-xl-1024-v1-0'
        }
        
        # Check if we have default models configured
        if 'image_generation' in self.config and 'default_models' in self.config['image_generation']:
            configured_default = self.config['image_generation']['default_models'].get(provider)
            if configured_default:
                return configured_default
        
        # If no configured default, return the provider-specific fallback
        return provider_defaults.get(provider)
    
    def get_default_size(self, provider: Optional[str] = None, model: Optional[str] = None) -> str:
        """Get default size for a provider/model.
        
        Args:
            provider: Provider to get size for
            model: Model to get size for
            
        Returns:
            Default size as a string (e.g., "1024x1024")
        """
        # Use config default if available
        default_size = self.config.get('image_generation', {}).get('default_size', "1024x1024")
        
        # Check provider/model specific defaults
        if provider or model:
            provider = provider or self.provider_name
            
            if provider.lower() == 'dalle':
                if model == 'dall-e-2':
                    return "1024x1024"  # DALL-E 2 standard size
                else:
                    # DALL-E 3 supports portrait sizes which look better in terminal
                    return "1024x1792"  # Portrait orientation works well for DALL-E
            elif provider.lower() == 'stability':
                # Stability AI works best with square images
                return "1024x1024"  # Square format for Stability AI
        
        return default_size
    
    def generate_image(self, prompt: str, model: Optional[str] = None, 
                     size: Optional[str] = None, quality: Optional[str] = None, 
                     style: Optional[str] = None) -> Dict[str, Any]:
        """Generate an image using the selected provider.
        
        Args:
            prompt: Text prompt for the image
            model: Model to use (provider-specific). If None, uses default.
            size: Image size (widthxheight)
            quality: Image quality (standard, hd)
            style: Style preset
            
        Returns:
            Provider-specific generation result
        """
        # Use provided model or get the default from config
        if model is None:
            model = self.get_default_model()
        
        # Use default size and quality if not provided
        if size is None:
            size = self.config.get('image_generation', {}).get('default_size', '1024x1024')
        if quality is None:
            quality = self.config.get('image_generation', {}).get('default_quality', 'standard')
        
        # For DALL-E provider
        if self.provider_name.lower() == 'dalle':
            return self.provider.generate_image(
                prompt=prompt,
                model=model,
                size=size,
                quality=quality,
                style=style or 'vivid'
            )
        
        # For Stability provider
        elif self.provider_name.lower() == 'stability':
            # Parse size into width and height
            try:
                width, height = map(int, size.split('x'))
            except ValueError:
                width, height = 1024, 1024
                
            return self.provider.generate_image(
                prompt=prompt,
                engine_id=model,
                width=width,
                height=height,
                style_preset=style
            )
        
        # Should never get here due to _get_provider validation
        raise ValueError(f"Unsupported provider: {self.provider_name}")
    
    def download_image(self, image_data: Dict[str, Any]) -> Path:
        """Download an image from generation result.
        
        Args:
            image_data: Image data from generation result
            
        Returns:
            Path to the downloaded image file
        """
        provider = image_data.get("provider", self.provider_name).lower()
        
        if provider == "dalle":
            # DALL-E returns a URL to download
            url = image_data.get("url")
            if not url:
                raise ValueError("No image URL found in DALL-E result")
            
            return self.provider.download_image(url)
            
        elif provider == "stability":
            # Stability returns base64-encoded image data
            b64_data = image_data.get("base64")
            if not b64_data:
                raise ValueError("No base64 image data found in Stability result")
            
            return self.provider.download_image(b64_data)
            
        raise ValueError(f"Unsupported provider: {provider}")
    
    def get_style_options(self, provider: Optional[str] = None) -> List[Dict[str, str]]:
        """Get available style options for a provider.
        
        Args:
            provider: Provider to get styles for (uses current if not provided)
            
        Returns:
            List of available styles with name and description
        """
        provider = provider or self.provider_name
        
        if provider.lower() == 'dalle':
            return [
                {
                    "id": "vivid",
                    "name": "Vivid",
                    "description": "Hyper-real and dramatic, with intense colors and contrast (default)"
                },
                {
                    "id": "natural",
                    "name": "Natural",
                    "description": "More muted and realistic, subtle and natural-looking results"
                }
            ]
        elif provider.lower() == 'stability':
            return [
                {
                    "id": "3d-model",
                    "name": "3D Model",
                    "description": "3D object rendering style"
                },
                {
                    "id": "analog-film",
                    "name": "Analog Film",
                    "description": "Classic film photography aesthetic"
                },
                {
                    "id": "anime",
                    "name": "Anime",
                    "description": "Japanese animation style"
                },
                {
                    "id": "cinematic",
                    "name": "Cinematic",
                    "description": "Film cinematography style with dramatic lighting"
                },
                {
                    "id": "comic-book",
                    "name": "Comic Book",
                    "description": "Comic book illustration style"
                },
                {
                    "id": "digital-art",
                    "name": "Digital Art",
                    "description": "Digital artwork style (default)"
                },
                {
                    "id": "enhance",
                    "name": "Enhance",
                    "description": "Enhanced and refined version of the prompt"
                },
                {
                    "id": "fantasy-art",
                    "name": "Fantasy Art",
                    "description": "Fantastical scenes and landscapes"
                },
                {
                    "id": "isometric",
                    "name": "Isometric",
                    "description": "Isometric technical illustration style"
                },
                {
                    "id": "line-art",
                    "name": "Line Art",
                    "description": "Simple line drawings"
                },
                {
                    "id": "low-poly",
                    "name": "Low Poly",
                    "description": "Low polygon 3D model aesthetic"
                },
                {
                    "id": "pixel-art",
                    "name": "Pixel Art",
                    "description": "Pixelated retro video game style"
                },
                {
                    "id": "photographic",
                    "name": "Photographic",
                    "description": "Realistic photography style"
                }
            ]
        
        return [] 