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
from cliche.utils.markdown_cleaner import clean_markdown_document

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
    
    # Initialize image data dictionary
    image_data = {"images": [], "credits": []}
    
    # Fetch images if requested
    if image or image_id:
        try:
            unsplash = UnsplashAPI()
            
            if image_id:
                # Get a specific image by ID
                console.print(f"🖼️ Getting image with ID: {image_id}...")
                photo_data = unsplash.get_photo_url(image_id, width=image_width)
                if photo_data:
                    # Add to image data
                    image_data["images"].append({
                        "url": photo_data["url"],
                        "alt_text": photo_data["alt_text"],
                        "width": image_width
                    })
                    image_data["credits"].append(get_photo_credit(photo_data, format))
            
            elif image:
                # Search for images by term
                console.print(f"🔍 Searching for '{image}' images...")
                results = unsplash.search_photos(image, per_page=image_count)
                
                # Check if we have results
                photos = results.get('results', [])
                if not photos:
                    console.print("❌ No images found for this search term.")
                else:
                    # Get image data for each photo in results
                    for i, photo in enumerate(photos[:image_count]):
                        photo_id = photo.get('id')
                        console.print(f"🖼️ Getting image {i+1}/{min(image_count, len(photos))}...")
                        
                        try:
                            photo_data = unsplash.get_photo_url(photo_id, width=image_width)
                            
                            # Add to image data
                            image_data["images"].append({
                                "url": photo_data["url"],
                                "alt_text": photo_data["alt_text"],
                                "width": image_width
                            })
                            image_data["credits"].append(get_photo_credit(photo, format))
                            
                        except Exception as e:
                            console.print(f"⚠️ Error getting image: {str(e)}")
            
        except Exception as e:
            console.print(f"⚠️ Error fetching images: {str(e)}")
            console.print("Continuing without images...")
    
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
        # Generate the basic content without showing API call details
        llm_response = await llm.generate_response(full_prompt, professional_mode=True)
        
        # Apply format-specific processing
        if format == "markdown":
            content = llm_response
            
            # Clean the markdown document
            content = clean_markdown_document(content)
            
        elif format == "html":
            content = llm_response
            
            # Just use the content as is for HTML for now
            # No clean_html_content function found in our search
        else:
            content = llm_response
            
        # Clean up any legacy [INSERT_IMAGE_X_HERE] placeholders that might appear
        content = re.sub(r'\[INSERT_IMAGE_\d+_HERE\]', '', content)
        
        # Process images if we have any
        if image_data["images"] and (format == 'markdown' or format == 'html'):
            # Check if any IMAGE_ placeholders are in the document
            placeholders_found = len(re.findall(r'\bIMAGE_\d+\b', content))
            
            # If no placeholders found, let's use LLM to suggest image placement
            if placeholders_found == 0:
                console.print("💡 Using AI-powered image placement to enhance the document...")
                
                # Split content into paragraphs for placement
                paragraphs = content.split('\n\n')
                
                # Get LLM recommendations for image placement
                insertion_points = None
                try:
                    insertion_points = await get_image_placement_suggestions(
                        llm=llm, 
                        document_content=content, 
                        image_count=len(image_data["images"]),
                        topic=full_prompt[:50],
                        format=format
                    )
                except Exception as e:
                    console.print(f"⚠️ Error getting image placement suggestions: {str(e)}")
                    insertion_points = None
                
                # If LLM suggestions aren't available or valid, fallback to our distribution method
                if not insertion_points:
                    # Find headings to identify section breaks
                    heading_indices = [i for i, p in enumerate(paragraphs) if p.startswith('#')]
                    
                    # If we have enough headings, distribute images after headings
                    if len(heading_indices) >= len(image_data["images"]):
                        # Choose evenly spaced heading indices
                        step = len(heading_indices) // (len(image_data["images"]) + 1)
                        if step < 1:
                            step = 1
                        
                        insertion_points = []
                        for i in range(1, len(image_data["images"]) + 1):
                            idx = min(i * step, len(heading_indices) - 1)
                            heading_idx = heading_indices[idx]
                            insertion_point = min(heading_idx + 1, len(paragraphs) - 1)
                            if insertion_point not in insertion_points:
                                insertion_points.append(insertion_point)
                    else:
                        # Not enough headings, distribute evenly throughout document
                        total_paragraphs = len(paragraphs)
                        spacing = total_paragraphs // (len(image_data["images"]) + 1)
                        
                        # Ensure we don't insert at the beginning
                        start_point = min(4, total_paragraphs // 10)
                        
                        insertion_points = []
                        for i in range(len(image_data["images"])):
                            # Calculate position ensuring even distribution
                            pos = start_point + (i + 1) * spacing
                            pos = min(pos, total_paragraphs - 1)
                            
                            # Avoid inserting before headings
                            if pos < total_paragraphs - 1 and paragraphs[pos + 1].startswith('#'):
                                pos += 2
                            
                            if pos not in insertion_points and pos < total_paragraphs:
                                insertion_points.append(pos)
                
                # Sort insertion points
                if insertion_points:
                    insertion_points.sort()
                    
                    # Make sure we don't have more insertion points than images
                    insertion_points = insertion_points[:len(image_data["images"])]
                    
                    # Insert images at the chosen points
                    for i, insertion_idx in enumerate(insertion_points):
                        if i < len(image_data["images"]):
                            img_data = image_data["images"][i]
                            img_alt = img_data["alt_text"] or "Image"
                            
                            if format == 'markdown':
                                img_content = f"\n\n![{img_alt}]({img_data['url']})\n\n"
                            else:  # HTML format
                                img_content = f"\n\n<img src=\"{img_data['url']}\" alt=\"{img_alt}\" style=\"max-width: 100%; height: auto;\">\n\n"
                                
                            paragraphs.insert(insertion_idx + i, img_content)
                    
                    # Reconstruct the document
                    content = '\n\n'.join(paragraphs)
            else:
                # Handle explicit placeholders
                console.print(f"🔄 Processing {placeholders_found} image placeholders...")
                
                # Replace placeholders with actual images
                for i, img_data in enumerate(image_data["images"]):
                    img_idx = i + 1
                    if img_idx <= placeholders_found:
                        placeholder = f"IMAGE_{img_idx}"
                        if format == 'markdown':
                            img_content = f"![{img_data['alt_text'] or 'Image'}]({img_data['url']})"
                        else:  # HTML
                            img_content = f"<img src=\"{img_data['url']}\" alt=\"{img_data['alt_text'] or 'Image'}\" style=\"max-width: 100%; height: auto;\">"
                        
                        content = content.replace(placeholder, img_content)
            
            # Add credits at the end of the document if we processed any images
            if image_data["credits"]:
                if format == 'markdown':
                    content += "\n\n---\n\n## Image Credits\n\n"
                    for credit in image_data["credits"]:
                        content += f"* {credit}\n"
                else:  # HTML
                    content += "\n\n<hr>\n<h2>Image Credits</h2>\n<ul>\n"
                    for credit in image_data["credits"]:
                        content += f"<li>{credit}</li>\n"
                    content += "</ul>\n"
        
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
