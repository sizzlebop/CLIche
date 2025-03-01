"""
DALL-E API utilities for CLIche.
Handles generating images using OpenAI's DALL-E models.
"""
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import click
from .file import get_output_dir, get_image_dir

class DALLEGenerator:
    """Wrapper for OpenAI's DALL-E API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the DALL-E API client.
        
        Args:
            api_key: Optional API key. If not provided, will try to get from environment.
        """
        # First try the provided API key
        self.api_key = api_key
        
        # If not provided, try to get from environment
        if not self.api_key:
            self.api_key = os.getenv('OPENAI_API_KEY')
        
        # If still not found, check the config file directly
        if not self.api_key:
            try:
                from ..core import Config
                config = Config()
                
                # Check for a dedicated DALL-E key
                if 'services' in config.config and 'dalle' in config.config['services']:
                    dalle_key = config.config['services']['dalle'].get('api_key')
                    if dalle_key:
                        self.api_key = dalle_key
            except Exception as e:
                # If there's any error loading the config, just continue
                pass
        
        # If API key is still not found, raise an error
        if not self.api_key:
            raise ValueError("OpenAI API key for DALL-E not found. Please configure it with 'cliche config --dalle-key YOUR_API_KEY'")
        
        self.api_base = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Version": "2020-11-07"  # Add API version header for compatibility
        }
        
        # Create image directory if it doesn't exist
        self.image_dir = get_image_dir()
    
    def generate_image(self, prompt: str, model: str = "dall-e-3", 
                       size: str = "1024x1024", quality: str = "standard", 
                       n: int = 1, style: str = "vivid") -> Dict[str, Any]:
        """Generate an image using DALL-E.
        
        Args:
            prompt: Text prompt for the image
            model: DALL-E model to use (dall-e-2, dall-e-3)
            size: Image size (1024x1024, 1792x1024, 1024x1792)
            quality: Image quality (standard, hd)
            n: Number of images to generate (1-4 for DALL-E 2, 1 for DALL-E 3)
            style: Image style (vivid, natural) - DALL-E 3 only
            
        Returns:
            Dictionary with generation results including image_path
        """
        url = f"{self.api_base}/images/generations"
        
        # Set default n value based on model to avoid API errors
        if model == "dall-e-3" and n > 1:
            n = 1  # DALL-E 3 only supports n=1
        
        # Ensure model format is correct (OpenAI is sometimes picky about exact format)
        # For DALL-E, OpenAI expects "dall-e-3" or "dall-e-2" 
        if model == "dalle-3" or model == "dalle3" or model == "dall-e3":
            model = "dall-e-3"
        elif model == "dalle-2" or model == "dalle2" or model == "dall-e2":
            model = "dall-e-2"
        
        # Print debug info
        print(f"Using model: {model}")
        
        data = {
            "prompt": prompt,
            "model": model,
            "n": n,
            "size": size,
            "quality": quality,
            "response_format": "url"
        }
        
        # Add style parameter for DALL-E 3
        if model == "dall-e-3":
            data["style"] = style
        
        # Debug: Print the request payload
        print(f"Request payload: {json.dumps(data, indent=2)}")
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            # Check for errors
            if response.status_code != 200:
                error_data = response.json()
                error_detail = error_data.get("error", {}).get("message", "Unknown error")
                error_type = error_data.get("error", {}).get("type", "")
                error_code = error_data.get("error", {}).get("code", "")
                
                # Detailed error message with helpful information
                error_message = f"DALL-E API Error ({response.status_code}): {error_detail}"
                
                # Add specific troubleshooting info based on error type
                if "content policy" in error_detail.lower():
                    error_message += "\nThe prompt may violate OpenAI's content policy. Try a different prompt."
                elif "authentication" in error_type or "auth" in error_type:
                    error_message += "\nAuthentication error. Check that your API key is valid and has not expired."
                elif "rate limit" in error_detail.lower():
                    error_message += "\nRate limit exceeded. Wait a moment before trying again."
                elif "billing" in error_detail.lower() or "quota" in error_detail.lower():
                    error_message += "\nYou've exceeded your quota or have insufficient funds. Check your OpenAI account."
                elif "invalid" in error_detail.lower() and "model" in error_detail.lower():
                    error_message += f"\nThe model '{model}' may not be available or accessible with your API key."
                
                # Print detailed error information for debugging
                print(f"Full API error response: {error_data}")
                
                raise Exception(error_message)
            
            # Process response data
            response_data = response.json()
            
            # Verify we have image data
            if not response_data.get('data'):
                raise Exception("No image data returned in response")
            
            first_image = response_data['data'][0]
            
            # Check if URL exists
            if 'url' not in first_image:
                raise Exception("No image URL in response data")
            
            # Download the image
            image_url = first_image['url']
            image_path = self.download_image(image_url)
            
            # Create a result dictionary
            result = {
                'provider': 'dalle',
                'model': model,
                'image_path': str(image_path)
            }
            
            # Add revised prompt if available (DALL-E 3 feature)
            if 'revised_prompt' in first_image:
                result['revised_prompt'] = first_image['revised_prompt']
            
            return result
            
        except requests.exceptions.ConnectionError:
            raise Exception("Network error: Could not connect to OpenAI API. Check your internet connection.")
        except requests.exceptions.Timeout:
            raise Exception("Timeout error: The request to OpenAI API timed out. Try again later.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError:
            raise Exception(f"Invalid response from OpenAI API: {response.text[:100]}...")
        except Exception as e:
            # Re-raise the exception with the original error message
            raise
    
    def download_image(self, url: str, filename: Optional[str] = None) -> Path:
        """Download an image from URL.
        
        Args:
            url: Image URL to download
            filename: Optional custom filename
            
        Returns:
            Path to the downloaded image file
        """
        # Generate default filename if not provided
        if not filename:
            import time
            timestamp = int(time.time())
            filename = f"dalle_{timestamp}.png"
        
        # Create output path
        output_path = self.image_dir / filename
        
        # Download the image
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return output_path
    
    def list_models(self) -> List[Dict[str, str]]:
        """List available DALL-E models.
        
        Returns:
            List of available models with name and description
        """
        return [
            {
                "id": "dall-e-3",
                "name": "DALL-E 3",
                "description": "Most capable image generation model with high resolution and detail"
            },
            {
                "id": "dall-e-2",
                "name": "DALL-E 2",
                "description": "Faster image generation with more variation options"
            }
        ] 