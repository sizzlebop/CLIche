"""
Stability AI utilities for CLIche.
Handles generating images using Stability AI's API.
"""
import os
import json
import base64
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import click
from .file import get_output_dir, get_image_dir

class StabilityGenerator:
    """Wrapper for Stability AI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Stability AI API client.
        
        Args:
            api_key: Optional API key. If not provided, will try to get from environment.
        """
        # First try the provided API key
        self.api_key = api_key
        
        # If not provided, try to get from environment
        if not self.api_key:
            self.api_key = os.getenv('STABILITY_API_KEY')
        
        # If still not found, check the config file directly
        if not self.api_key:
            try:
                from ..core import Config
                config = Config()
                if 'services' in config.config and 'stability_ai' in config.config['services']:
                    self.api_key = config.config['services']['stability_ai'].get('api_key')
            except Exception as e:
                # If there's any error loading the config, just continue
                pass
        
        # If API key is still not found, raise an error
        if not self.api_key:
            raise ValueError("Stability AI API key not found. Please configure it with 'cliche config --stability-key YOUR_API_KEY'")
        
        self.api_base = "https://api.stability.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Create image directory if it doesn't exist
        self.image_dir = get_image_dir()
    
    def list_engines(self) -> List[Dict[str, Any]]:
        """List available engines from Stability AI.
        
        Returns:
            List of available engines with their details
        """
        url = f"{self.api_base}/v1/engines/list"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            # Check for errors
            if response.status_code != 200:
                error_data = response.json() if response.content else {"message": "Empty response"}
                error_detail = error_data.get("message", "Unknown error")
                raise Exception(f"Error listing engines: {error_detail}")
            
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise
    
    def generate_image(self, prompt: str, engine_id: str = "stable-diffusion-xl-1024-v1-0", 
                       width: int = 1024, height: int = 1024, 
                       cfg_scale: float = 7.0, style_preset: Optional[str] = None,
                       steps: int = 30, samples: int = 1) -> Dict[str, Any]:
        """Generate an image using Stability AI.
        
        Args:
            prompt: Text prompt for the image
            engine_id: Engine ID to use
            width: Image width
            height: Image height
            cfg_scale: How strictly the diffusion process adheres to the prompt (1-35)
            style_preset: Style preset to use (None, 3d-model, analog-film, etc.)
            steps: Number of diffusion steps to run (10-150)
            samples: Number of images to generate (1-10)
            
        Returns:
            Dictionary with generation results
        """
        url = f"{self.api_base}/v1/generation/{engine_id}/text-to-image"
        
        data = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": cfg_scale,
            "height": height,
            "width": width,
            "samples": samples,
            "steps": steps
        }
        
        # Add style preset if provided
        if style_preset:
            data["style_preset"] = style_preset
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            
            # Check for errors
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_detail = error_data.get("message", "Unknown error")
                    
                    # Check specifically for dimension-related errors
                    if "dimensions" in error_detail.lower() or "512" in error_detail:
                        # This is a dimension restriction error
                        model_name = engine_id
                        
                        # Custom error message with clear guidance
                        error_message = f"Error generating image: {error_detail}\n\n"
                        error_message += "📏 Dimension Restrictions 📏\n"
                        error_message += f"The model '{model_name}' has specific dimension requirements:\n"
                        
                        if "beta" in engine_id.lower():
                            error_message += "- Only one dimension can exceed 512px\n"
                            error_message += "- Valid examples: 512x768, 768x512, 512x512\n"
                            error_message += "- Invalid examples: 768x768, 1024x1024\n"
                        else:
                            error_message += "- Check model-specific dimension requirements\n"
                        
                        error_message += "\nTo fix this, try:\n"
                        error_message += "1. Use valid dimensions: cliche image \"your prompt\" --generate --size 512x768\n"
                        error_message += "2. Switch to SDXL model: cliche config --image-provider stability --image-model stable-diffusion-xl-1024-v1-0\n"
                        error_message += "3. Use DALL-E: cliche image \"your prompt\" --generate --provider dalle"
                        
                        raise Exception(error_message)
                    else:
                        raise Exception(f"Error generating image: {error_detail}")
                except ValueError:
                    # Response may not be valid JSON
                    raise Exception(f"Error generating image: Status code {response.status_code}")
                
            # Only try to parse the response as JSON if we got a success status
            response_data = response.json()
            
            # Validate that the response has the expected structure
            if not response_data.get("artifacts"):
                raise Exception("No image data returned in response")
            
            # Process the response
            first_image = response_data["artifacts"][0]
            
            # Truncate the base64 data for logging purposes
            if "base64" in first_image:
                base64_data = first_image["base64"]
                first_image["base64_preview"] = base64_data[:30] + "..." if base64_data else None
            
            # Download the image
            image_path = self.download_image(first_image["base64"])
            
            # Return a result dictionary similar to DALL-E
            return {
                "provider": "stability",
                "model": engine_id,
                "image_path": str(image_path)
            }
        
        except requests.exceptions.ConnectionError:
            raise Exception("Network error: Could not connect to Stability AI API. Check your internet connection.")
        except requests.exceptions.Timeout:
            raise Exception("Timeout error: The request to Stability AI API timed out. Try again later.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError:
            raise Exception(f"Invalid response from Stability AI API - could not parse as JSON")
        except Exception as e:
            # Re-raise the exception with the original error message
            # but make sure not to include any base64 data in the error message
            error_message = str(e)
            if len(error_message) > 500 and "," in error_message:
                # Likely contains base64 data, truncate it
                raise Exception(f"{error_message[:500]}... [truncated error message]")
            raise
    
    def download_image(self, base64_data: str, filename: Optional[str] = None) -> Path:
        """Save a base64 encoded image to file.
        
        Args:
            base64_data: Base64 encoded image data
            filename: Optional custom filename
            
        Returns:
            Path to the saved image file
        """
        # Generate default filename if not provided
        if not filename:
            import time
            timestamp = int(time.time())
            filename = f"stability_{timestamp}.png"
        
        # Create output path
        output_path = self.image_dir / filename
        
        # Decode and save the image
        image_data = base64.b64decode(base64_data)
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        return output_path
    
    def list_models(self) -> List[Dict[str, str]]:
        """List available Stability AI models.
        
        Returns:
            List of available models with name and description
        """
        # Create our comprehensive known models list
        known_models = [
            # SDXL Models
            {
                "id": "stable-diffusion-xl-1024-v1-0",
                "name": "Stable Diffusion XL v1.0",
                "description": "Stability-AI Stable Diffusion XL v1.0 - State-of-the-art image generation at 1024x1024 resolution"
            },
            {
                "id": "stable-diffusion-xl-beta-v2-2-2",
                "name": "Stable Diffusion XL Beta v2.2.2",
                "description": "Improved version of SDXL with better image quality"
            },
            # SD3 Models
            {
                "id": "stable-diffusion-3",
                "name": "Stable Diffusion 3",
                "description": "Stability-AI's latest generation with improved quality and coherence"
            },
            {
                "id": "stable-diffusion-3-medium",
                "name": "Stable Diffusion 3 Medium",
                "description": "Medium-sized version of SD3 with balanced performance and quality"
            },
            # SD Legacy Models
            {
                "id": "stable-diffusion-v1-6",
                "name": "Stable Diffusion v1.6",
                "description": "Stability-AI Stable Diffusion v1.6 - Legacy model for 512x512 resolution"
            },
            {
                "id": "stable-diffusion-512-v2-1",
                "name": "Stable Diffusion v2.1",
                "description": "Stability-AI Stable Diffusion v2.1 - Optimized for 512x512 resolution generation"
            },
            {
                "id": "stable-diffusion-768-v2-1",
                "name": "Stable Diffusion v2.1-768",
                "description": "Stability-AI Stable Diffusion v2.1 - Higher resolution version at 768x768"
            },
            # Specialized Models
            {
                "id": "stable-video-diffusion",
                "name": "Stable Video Diffusion",
                "description": "Generates short video clips from image and text prompts"
            },
            {
                "id": "sdxl-turbo",
                "name": "SDXL Turbo",
                "description": "Faster version of SDXL optimized for real-time generation"
            },
            {
                "id": "esrgan-v1-x2plus",
                "name": "ESRGAN v1 x2Plus",
                "description": "Image upscaling model for enhancing image resolution"
            },
            # Community-based or fine-tuned models
            {
                "id": "dreamshaper-8",
                "name": "Dreamshaper v8",
                "description": "Community model fine-tuned for artistic and creative results"
            },
            {
                "id": "realistic-vision-v5",
                "name": "Realistic Vision v5", 
                "description": "Specialized for photorealistic image generation"
            },
            {
                "id": "sdxl-lightning",
                "name": "SDXL Lightning",
                "description": "Ultra-fast SDXL variant optimized for speed"
            },
            {
                "id": "deliberate-v2",
                "name": "Deliberate v2",
                "description": "Fine-tuned model focused on detailed, deliberate compositions"
            },
            {
                "id": "protogen-v5.3",
                "name": "Protogen v5.3",
                "description": "All-purpose fine-tuned model with excellent color and composition"
            },
            {
                "id": "anything-v5",
                "name": "Anything v5",
                "description": "Versatile model optimized for anime and illustration styles"
            },
            {
                "id": "openjourney-v4",
                "name": "Openjourney v4",
                "description": "Midjourney-inspired aesthetic for unique artistic styles"
            },
            {
                "id": "juggernautxl-v10",
                "name": "JuggernautXL v10",
                "description": "Powerful all-around model with excellent composition and detail rendering"
            }
        ]
        
        try:
            # Try to get models from API
            engines = self.list_engines()
            api_models = []
            
            # Create mapping of existing model IDs for quick lookup
            known_model_ids = {model["id"]: True for model in known_models}
            
            # Add API models to the result list if they're not already in our known models
            for engine in engines:
                engine_id = engine.get("id")
                if engine_id and engine_id not in known_model_ids:
                    api_models.append({
                        "id": engine_id,
                        "name": engine.get("name", engine_id),
                        "description": engine.get("description", "API-provided model")
                    })
            
            # Combine API models with our known models
            # API models are added first so they appear at the top of the list
            return api_models + known_models
            
        except Exception:
            # If failed to get actual engines, return just our known models
            return known_models 