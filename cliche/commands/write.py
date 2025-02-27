"""
Text generation command for CLIche.
Simplified interface for generating text content in various formats.
"""
import click
import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from ..core import cli, get_llm
from ..utils.file import save_text_to_file, get_docs_dir, get_unique_filename
from ..utils.unsplash import UnsplashAPI, format_image_for_markdown, format_image_for_html, get_photo_credit
import re  # Add this import at the top if it's not already there

# Initialize console for rich output
console = Console()

@cli.command()
@click.argument('prompt', nargs=-1, required=True)
@click.option('--format', '-f', type=click.Choice(['text', 'markdown', 'html']), default='text',
              help='Format of content to generate')
@click.option('--path', '-p', help='Optional path to save the file', type=click.Path())
@click.option('--image', '-i', help='Add an image by Unsplash search term', type=str)
@click.option('--image-id', help='Add a specific Unsplash image by ID', type=str)
@click.option('--image-count', default=1, help='Number of images to add (for search term)', type=int)
@click.option('--image-width', default=800, help='Width of images', type=int)
def write(prompt: tuple[str, ...], format: str, path: Optional[str], 
          image: Optional[str], image_id: Optional[str], image_count: int, image_width: int):
    """Generate text content in various formats.
    
    Examples:
        cliche write a tutorial on docker --format markdown
        cliche write a blog post about AI --format html
        cliche write a project readme --format markdown --image "coding setup"
        cliche write meeting notes from today
        cliche write a travel guide to Paris --format markdown --image "paris" --image-count 3
    """
    # Run async code in sync context
    asyncio.run(async_write(prompt, format, path, image, image_id, image_count, image_width))

async def async_write(prompt: tuple[str, ...], format: str, path: Optional[str],
                     image: Optional[str], image_id: Optional[str], image_count: int, image_width: int):
    """Async implementation of write command."""
    # Join the prompt parts
    full_prompt = ' '.join(prompt)
    
    # Get format-specific extension
    if format == 'markdown':
        ext = '.md'
    elif format == 'html':
        ext = '.html'
    else:
        ext = f'.{format}'
    
    # Get default filename if path not provided
    if not path:
        # Create a filename from the first few words of the prompt
        words = full_prompt.lower().split()[:3]
        base_filename = '_'.join(words) + ext
        # Use the docs/write directory for organization
        output_dir = get_docs_dir('write')
        # Get a unique filename
        unique_filename = get_unique_filename(output_dir, base_filename)
        path = str(output_dir / unique_filename)
    
    # Initialize image data dictionary - SIMPLIFIED FOR TESTING
    image_data = {"images": [], "credits": []}
    
    # SIMPLIFIED: Skip image fetching for testing
    
    # Add format-specific instructions
    format_instructions = {
        'text': 'Write this as a plain text document without any special formatting.',
        'markdown': 'Write this as a markdown document with proper formatting. Use markdown features like headings, lists, code blocks, bold, italic, and links as appropriate.',
        'html': 'Write this as an HTML document with proper tags and structure.'
    }[format]
    
    full_prompt = f"{format_instructions}\n\n{full_prompt}"
    
    # Get the LLM instance
    llm = get_llm()
    
    console.print("🔄 Generating content...")
    
    try:
        # SIMPLIFIED: Just generate the basic content
        console.print("🔄 Calling LLM API...")
        content = await llm.generate_response(full_prompt, professional_mode=True)
        console.print("✅ Received response from LLM")
        
        # SIMPLIFIED: Skip all the complex processing for testing
        
        # Save to file
        save_text_to_file(content, path)
        console.print(f"✅ Content saved to: {path}")
        return
        
    except Exception as e:
        console.print(f"❌ Error generating content: {str(e)}")
        return

async def get_image_placement_suggestions(llm, document_content, image_count, topic, format):
    """Ask the LLM to suggest optimal image placement locations in the document.
    
    Args:
        llm: The LLM instance to use
        document_content: The content of the document to analyze
        image_count: Number of images to place
        topic: The document topic
        format: The document format (markdown, html)
        
    Returns:
        A list of suggested paragraph indices where images should be placed
    """
    # Create a prompt specifically for image placement
    placement_prompt = f"""
    I've generated a {format} document about "{topic}". Now I need to place {image_count} images at optimal locations.
    
    Please analyze this document and suggest the {image_count} best locations to place relevant images.
    
    For each suggested location:
    1. Identify the paragraph number (counting from 0)
    2. Explain why this is a good location (e.g., introduces a key concept, visualizes an example)
    
    Your response should be in this format:
    PLACEMENT 1: Paragraph X - Reason
    PLACEMENT 2: Paragraph Y - Reason
    ... and so on
    
    Here's the document content:
    ---
    {document_content}
    ---
    
    IMPORTANT: Focus on finding contextually relevant placements where images would enhance understanding.
    """
    
    # Get suggestions from the LLM
    response = await llm.generate_response(placement_prompt, professional_mode=True)
    
    # Parse the response to extract paragraph indices
    suggested_indices = []
    
    # Look for "PLACEMENT X: Paragraph Y" patterns
    placement_pattern = r'PLACEMENT\s+\d+\s*:\s*Paragraph\s+(\d+)'
    matches = re.finditer(placement_pattern, response)
    
    for match in matches:
        try:
            paragraph_index = int(match.group(1))
            suggested_indices.append(paragraph_index)
        except:
            continue
    
    # If we couldn't extract valid suggestions, fallback to evenly distributed placements
    if not suggested_indices or len(suggested_indices) < image_count:
        # Our existing fallback method which evenly distributes images
        return None
    
    # Return only up to the requested number of placements
    return suggested_indices[:image_count]
