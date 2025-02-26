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
from ..utils.file import save_text_to_file, get_output_dir
from ..utils.unsplash import UnsplashAPI, format_image_for_markdown, format_image_for_html, get_photo_credit
import re  # Add this import at the top if it's not already there

# Initialize console for rich output
console = Console()

@cli.command()
@click.argument('prompt', nargs=-1, required=True)
@click.option('--format', '-f', type=click.Choice(['text', 'markdown', 'html']), default='text',
              help='Type of content to generate')
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
        filename = '_'.join(words) + ext
        # Use the .cliche/files/docs directory
        output_dir = get_output_dir('write')
        path = str(output_dir / filename)
    
    # Initialize image data dictionary
    image_data = {"images": [], "credits": []}
    
    # Handle image fetching if requested
    if image or image_id:
        try:
            unsplash = UnsplashAPI()
            
            if image_id:
                # Fetch specific image by ID
                console.print(f"🖼️ Getting image with ID: {image_id}...")
                photo_data = unsplash.get_photo_url(image_id, width=image_width)
                
                # Add to image data
                image_data["images"].append({
                    "url": photo_data["url"],
                    "alt_text": photo_data["alt_text"],
                    "width": image_width
                })
                image_data["credits"].append(get_photo_credit({
                    "user": {
                        "name": photo_data["photographer_name"],
                        "username": photo_data["photographer_username"]
                    }
                }, format))
                
            elif image:
                # Search for images by term
                console.print(f"🔍 Searching for '{image}' images...")
                results = unsplash.search_photos(image, per_page=image_count)
                
                # Check if we have results
                photos = results.get('results', [])
                if not photos:
                    console.print("❌ No images found for this search term.")
                else:
                    # Get URL for each image instead of downloading
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
        'markdown': 'Write this as a markdown document with proper formatting. Use markdown features like headings, lists, code blocks, bold, italic, and links as appropriate. Format your response using rich markdown syntax. IMPORTANT: Do NOT include ```markdown or any backtick fences at the beginning or end of the document.',
        'html': 'Write this as an HTML document with proper tags and structure.'
    }[format]
    
    # Add extra instructions for image placement if we have images
    if image_data["images"] and (format == 'markdown' or format == 'html'):
        format_instructions += f"""

Include {len(image_data['images'])} relevant image placeholders where appropriate in the content.
IMPORTANT: Use exactly these placeholder formats:
- For markdown: ![Image Description](IMAGE_{1}) for the first image, ![Image Description](IMAGE_{2}) for the second, etc.
- For HTML: <img src="IMAGE_{1}" alt="Image Description"> for the first image, etc.
"""
    
    full_prompt = f"{format_instructions}\n\n{full_prompt}"
    
    # Get the LLM instance
    llm = get_llm()
    
    console.print("🔄 Generating content...")
    
    try:
        # Generate content - use professional mode for document generation
        content = await llm.generate_response(full_prompt, professional_mode=True)
        
        # Process the generated content to replace image placeholders
        if image_data["images"] and (format == 'markdown' or format == 'html'):
            print(f"Processing {len(image_data['images'])} images for document")
            
            for i, img_data in enumerate(image_data["images"]):
                # 1-indexed for placeholders
                img_idx = i + 1
                
                if format == 'markdown':
                    # Try to find patterns with IMAGE placeholder in various formats
                    img_placeholder_patterns = [
                        r'!\[([^\]]+)\]\(IMAGE_{}\)'.format(img_idx),  # ![Alt text](IMAGE_n)
                        r'!\[([^\]]+)\]!\[([^\]]+)\]\(/[^)]+\)'.format(img_idx),  # ![Alt]![Description](/path)
                        r'!\[([^\]]+)\]IMAGE_{}'.format(img_idx),  # ![Alt]IMAGE_n
                        r'!\[([^\]]+)\]\[IMAGE_{}\]'.format(img_idx),  # ![Alt][IMAGE_n]
                        r'\(IMAGE_{}\)'.format(img_idx),  # (IMAGE_n)
                        r'IMAGE_{}'.format(img_idx)  # IMAGE_n plain
                    ]
                    
                    # Format for Markdown
                    img_tag = format_image_for_markdown(
                        img_data["url"], 
                        img_data["alt_text"], 
                        img_data["width"]
                    )
                    
                    # First try these exact patterns
                    image_replaced = False
                    for pattern in img_placeholder_patterns:
                        print(f"Looking for pattern: {pattern}")
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            image_replaced = True
                            full_match = match.group(0)
                            
                            # Get the alt text if available, or use a default
                            try:
                                alt_text = match.group(1) if match.lastindex and match.lastindex >= 1 else "Image"
                            except:
                                alt_text = "Image"
                                
                            # Create proper markdown image
                            proper_image = f"![{alt_text}]({img_data['url']})"
                            print(f"Replacing '{full_match}' with '{proper_image}'")
                            content = content.replace(full_match, proper_image)
                    
                    # If no pattern matched, fall back to simple replacement
                    if not image_replaced:
                        print(f"No complex patterns matched for image {img_idx}, trying simple replacements")
                        # Try simple replacements
                        replacements = [
                            (f"(IMAGE_{img_idx})", f"({img_data['url']})"),
                            (f"[IMAGE_{img_idx}]", f"[{img_data['url']}]"),
                            (f"IMAGE_{img_idx}", img_data["url"])
                        ]
                        
                        for old, new in replacements:
                            if old in content:
                                print(f"Replacing {old} with {new}")
                                content = content.replace(old, new)
                                image_replaced = True
                                break
                        
                    if not image_replaced:
                        print(f"Unable to find any placeholder for image {img_idx}")
                
                elif format == 'html':
                    # Format for HTML
                    img_tag = format_image_for_html(
                        img_data["url"], 
                        img_data["alt_text"], 
                        img_data["width"]
                    )
                    
                    # Primary placeholder format: src="IMAGE_{n}"
                    primary_placeholder = f"IMAGE_{img_idx}"
                    if primary_placeholder in content:
                        print(f"Replacing {primary_placeholder} with {img_data['url']}")
                        content = content.replace(primary_placeholder, img_data["url"])
                    else:
                        # Try to find <img src="IMAGE_n" patterns
                        img_html_pattern = r'<img[^>]*src=["\'](IMAGE_{})["\'][^>]*>'.format(img_idx)
                        matches = re.finditer(img_html_pattern, content)
                        img_replaced = False
                        for match in matches:
                            img_replaced = True
                            full_match = match.group(0)
                            # Replace just the src attribute
                            new_img_tag = full_match.replace(f'src="{primary_placeholder}"', f'src="{img_data["url"]}"')
                            content = content.replace(full_match, new_img_tag)
                            print(f"Replaced HTML img tag: {full_match} with {new_img_tag}")
                        
                        if not img_replaced:
                            print(f"Cannot find {primary_placeholder} in HTML, tried pattern: {img_html_pattern}")
            
            # Add credits at the end of the document
            if image_data["credits"]:
                if format == 'markdown':
                    content += "\n\n---\n\n## Image Credits\n\n"
                    for credit in image_data["credits"]:
                        content += f"* {credit}\n"
                else:
                    content += "\n\n<hr>\n<h2>Image Credits</h2>\n<ul>\n"
                    for credit in image_data["credits"]:
                        content += f"<li>{credit}</li>\n"
                    content += "</ul>\n"
        
        # Add HTML wrapper if it's HTML and doesn't have one already
        if format == 'html' and not content.strip().startswith('<!DOCTYPE html>'):
            content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Content</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        img {{ max-width: 100%; height: auto; display: block; margin: 20px 0; }}
        code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        h1, h2, h3 {{ color: #333; }}
        .unsplash-image {{ border-radius: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
{content}
</body>
</html>"""
        
        # Save to file
        save_text_to_file(content, path)
        console.print(f"✅ Content saved to: {path}")
        
        # Display image info if added
        if image_data["images"]:
            console.print(f"🖼️ Added {len(image_data['images'])} image(s) to the document")
        
    except Exception as e:
        console.print(f"❌ Error generating content: {str(e)}")
