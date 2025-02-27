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
def config(provider: Optional[str], api_key: Optional[str], model: Optional[str], 
           unsplash_key: Optional[str], brave_key: Optional[str]):
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
