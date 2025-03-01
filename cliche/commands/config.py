"""
Configuration management commands
"""
import click
import asyncio
import os
from typing import Optional
from ..core import Config, LLMProvider, CLIche

@click.command()
@click.option('--provider', type=click.Choice([p.value for p in LLMProvider]), help='Set active LLM provider')
@click.option('--api-key', help='API key for the provider')
@click.option('--model', help='Model to use')
@click.option('--unsplash-key', help='API key for Unsplash image service')
@click.option('--brave-key', help='API key for Brave Search service')
@click.option('--stability-key', help='API key for Stability AI image generation')
@click.option('--dalle-key', help='Configure DALL-E to use a specific API key')
@click.option('--image-provider', type=click.Choice(['dalle', 'stability']), help='Set default image generation provider')
@click.option('--image-model', help='Set default model for the image provider')
def config(provider: Optional[str], api_key: Optional[str], model: Optional[str], 
           unsplash_key: Optional[str], brave_key: Optional[str],
           stability_key: Optional[str], dalle_key: Optional[str],
           image_provider: Optional[str], image_model: Optional[str]):
    """Configure CLIche settings"""
    config = Config()
    
    # Handle Unsplash API key
    if unsplash_key:
        # Set Unsplash API key in config
        if 'services' not in config.config:
            config.config['services'] = {}
        if 'unsplash' not in config.config['services']:
            config.config['services']['unsplash'] = {}
        
        config.config['services']['unsplash']['api_key'] = unsplash_key
        
        # Also set in environment for current session
        os.environ['UNSPLASH_API_KEY'] = unsplash_key
        click.echo("🖼️ Unsplash API key configured successfully.")
    
    # Handle Brave Search API key
    if brave_key:
        # Set Brave Search API key in config
        if 'services' not in config.config:
            config.config['services'] = {}
        if 'brave_search' not in config.config['services']:
            config.config['services']['brave_search'] = {}
        
        config.config['services']['brave_search']['api_key'] = brave_key
        
        # Also set in environment for current session
        os.environ['BRAVE_SEARCH_API_KEY'] = brave_key
        click.echo("🔍 Brave Search API key configured successfully.")
    
    # Handle Stability AI API key
    if stability_key:
        # Set Stability AI key in config
        if 'services' not in config.config:
            config.config['services'] = {}
        if 'stability_ai' not in config.config['services']:
            config.config['services']['stability_ai'] = {}
        
        config.config['services']['stability_ai']['api_key'] = stability_key
        
        # Also set in environment for current session
        os.environ['STABILITY_API_KEY'] = stability_key
        click.echo("🎨 Stability AI API key configured successfully.")
    
    # Configure DALL-E with a specific key
    if dalle_key:
        # Set DALL-E key in config
        if 'services' not in config.config:
            config.config['services'] = {}
        if 'dalle' not in config.config['services']:
            config.config['services']['dalle'] = {}
        
        # Set the API key and remove any legacy fields
        config.config['services']['dalle']['api_key'] = dalle_key
        if 'use_openai_key' in config.config['services']['dalle']:
            del config.config['services']['dalle']['use_openai_key']
        
        # Also set in environment for current session
        os.environ['OPENAI_API_KEY'] = dalle_key
        click.echo("🖌️ DALL-E API key configured successfully.")
    
    # Ensure image_generation section exists
    if 'image_generation' not in config.config:
        config.config['image_generation'] = {
            "default_provider": "dalle",  # Options: dalle, stability
            "default_size": "1024x1024",
            "default_quality": "standard"  # Options: standard, hd
        }
    
    # Special handling: if user provides --image-provider and --model, they likely meant --image-model
    if image_provider and model and not image_model:
        # They likely meant to set the image model but used --model instead of --image-model
        image_model = model
        click.echo(f"⚠️ Note: Using --model with --image-provider likely meant to set the image model.")
        click.echo(f"⚠️ Applied '{model}' as the image model. In the future, use --image-model for clarity.")
    
    # Configure default image provider
    if image_provider:
        config.config['image_generation']['default_provider'] = image_provider
        click.echo(f"🖼️ Default image provider set to {image_provider}.")
        
        # If default model is also provided, update it
        if image_model:
            if 'default_models' not in config.config['image_generation']:
                config.config['image_generation']['default_models'] = {}
            
            config.config['image_generation']['default_models'][image_provider] = image_model
            click.echo(f"🖼️ Default model for {image_provider} set to {image_model}.")
    # If only default model is provided without provider, use the current default provider
    elif image_model:
        current_provider = config.config['image_generation']['default_provider']
        if 'default_models' not in config.config['image_generation']:
            config.config['image_generation']['default_models'] = {}
        
        config.config['image_generation']['default_models'][current_provider] = image_model
        click.echo(f"🖼️ Default model for {current_provider} set to {image_model}.")
    
    # Handle provider updates
    if provider:
        config.config['provider'] = provider
        
        # Initialize provider config if it doesn't exist
        if provider not in config.config['providers']:
            config.config['providers'][provider] = {}
            
        # Update model if provided
        if model:
            config.config['providers'][provider]['model'] = model
            
        # Update API key if provided
        if api_key:
            config.config['providers'][provider]['api_key'] = api_key
    elif model or api_key:
        # If no provider specified, use active provider
        active_provider = config.config['provider']
        if model:
            config.config['providers'][active_provider]['model'] = model
        if api_key:
            config.config['providers'][active_provider]['api_key'] = api_key

    config.save_config(config.config)
    
    # Add clear instructions for common commands
    if image_provider or image_model:
        click.echo("\n📝 Image generation configuration:")
        click.echo("  • To generate an image: cliche image \"your prompt\" --generate")
        click.echo("  • To set image size: cliche image \"your prompt\" --generate --size 512x768")
        click.echo("  • To see all image models: cliche image --list-models")
    
    click.echo("✨ Configuration updated. I'll try to be less judgy (no promises).")

@click.command()
@click.option('--provider', type=click.Choice([p.value for p in LLMProvider]), help='Provider to list models for')
def models(provider: Optional[str]):
    """List available models for the specified or active provider"""
    config = Config()
    current_config = config.config
    
    # Use specified provider or active provider
    provider_name = provider or current_config["provider"]
    
    # Create a new config instance for the specified provider
    temp_config = Config()
    temp_config.config["provider"] = provider_name
    
    # Create CLIche instance with temporary config
    cliche = CLIche()
    cliche.config = temp_config
    provider_instance = cliche._get_provider()
    
    try:
        # Get models from provider
        models = asyncio.run(provider_instance.list_models())
        
        if not models:
            click.echo(f"No models found for {provider_name}")
            return
            
        click.echo(f"\nAvailable Models for {provider_name}:")
        for model_id, description in models:
            click.echo(f"- {model_id}: {description}")
            
    except Exception as e:
        click.echo(f"Error listing models: {str(e)}")
