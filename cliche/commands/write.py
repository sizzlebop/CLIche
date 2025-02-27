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
        'markdown': '''Write this as a markdown document with proper formatting. Use markdown features like headings, lists, code blocks, bold, italic, and links as appropriate.

For code blocks, follow these strict formatting rules:
1. ALWAYS use three backticks (```) to open AND close every code block
2. ALWAYS specify a language (e.g., ```python, ```bash) for syntax highlighting
3. ALWAYS include a blank line before AND after each code block
4. NEVER have text directly adjacent to the opening or closing fence
5. ALWAYS close code blocks before starting new paragraphs or sections
6. When showing examples with code, ALWAYS close the code block before continuing with explanations

EXTREMELY IMPORTANT: When showing examples, don't write phrases like "For example:" and then start a code block without closing it. Always close all code blocks even when explaining examples.

For example (correct formatting):
```python
print("Hello, world!")
```

This is text outside the code block, explaining the example.

IMPORTANT: Do NOT include ```markdown or any backtick fences at the beginning or end of the document.''',
        'html': '''Write this as an HTML document with proper tags and structure. The ENTIRE content must use proper HTML tags, not Markdown.

EXTREMELY IMPORTANT: You MUST use HTML tags for EVERYTHING and NEVER use Markdown syntax anywhere in your response.
For example:
- CORRECT: <h1>Main Heading</h1>
- INCORRECT: # Main Heading

- CORRECT: <h2>Section Heading</h2>
- INCORRECT: ## Section Heading

- CORRECT: <p>This is a paragraph with <strong>bold text</strong>.</p>
- INCORRECT: This is a paragraph with **bold text**.

- CORRECT: <ul><li>List item</li><li>Another item</li></ul>
- INCORRECT: - List item
             - Another item

DO NOT EVER USE # FOR HEADINGS OR ** FOR BOLD TEXT OR - FOR LISTS. Always use proper HTML tags like <h1>, <strong>, <ul><li>, etc.

Every single piece of content must be enclosed in appropriate HTML tags. Do not mix HTML and Markdown syntax anywhere.'''
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
        
        # Clean up any stray markdown code fences from HTML content
        if format == 'html':
            # Remove any markdown code fences that might appear in the HTML content
            content = re.sub(r'```html\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            
            # Also attempt to convert any remaining Markdown to HTML
            # Convert headings (all levels h1-h6)
            content = re.sub(r'^#{1}\s+(.+?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
            content = re.sub(r'^#{2}\s+(.+?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
            content = re.sub(r'^#{3}\s+(.+?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
            content = re.sub(r'^#{4}\s+(.+?)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)
            content = re.sub(r'^#{5}\s+(.+?)$', r'<h5>\1</h5>', content, flags=re.MULTILINE)
            content = re.sub(r'^#{6}\s+(.+?)$', r'<h6>\1</h6>', content, flags=re.MULTILINE)
            
            # Convert bold text
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            
            # Convert italic text
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            
            # Convert list items
            content = re.sub(r'^\s*-\s+(.+?)$', r'<li>\1</li>', content, flags=re.MULTILINE)
            
            # Wrap adjacent list items in <ul> tags
            list_pattern = r'(<li>.*?</li>\s*){2,}'
            matches = re.finditer(list_pattern, content, re.DOTALL)
            for match in matches:
                orig = match.group(0)
                wrapped = f'<ul>{orig}</ul>'
                content = content.replace(orig, wrapped)
            
            # Ensure all paragraphs are wrapped in <p> tags
            # Find text that's not inside any HTML tags and wrap it with <p>
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() and not re.match(r'^\s*<', line) and not re.match(r'^\s*$', line):
                    # If it's not already in an HTML tag, wrap it
                    lines[i] = f'<p>{line}</p>'
            content = '\n'.join(lines)
        
        # Process the generated content to replace image placeholders
        if image_data["images"] and (format == 'markdown' or format == 'html'):
            print(f"Processing {len(image_data['images'])} images for document")
            
            # Check if any IMAGE_ string appears at all in the document
            all_image_indicators = len(re.findall(r'IMAGE_\d+', content))
            
            # If no placeholders found, let's use LLM-based image placement
            if all_image_indicators == 0:
                print("💡 Using AI-powered image placement to find optimal locations...")
                
                # Split content into paragraphs for placement
                paragraphs = content.split('\n\n')
                
                # Get LLM recommendations for image placement
                insertion_points = None
                try:
                    # Get a topic from the content
                    topic = ' '.join(prompt)
                    title_match = re.search(r'^# (.+)', content, re.MULTILINE)
                    if title_match:
                        topic = title_match.group(1)
                        
                    # Get suggestions from the LLM
                    insertion_points = await get_image_placement_suggestions(
                        llm=llm,
                        document_content=content,
                        image_count=len(image_data["images"]),
                        topic=topic,
                        format=format
                    )
                except Exception as e:
                    print(f"⚠️ Error getting image placement suggestions: {str(e)}")
                    insertion_points = None
                
                # If LLM suggestions aren't available or valid, fallback to our distribution method
                if not insertion_points:
                    print("⚠️ Couldn't get valid placement suggestions, falling back to evenly distributed images...")
                    
                    # Find headings to identify section breaks
                    heading_indices = [i for i, p in enumerate(paragraphs) if p.startswith('#')]
                    
                    # If we have enough headings, distribute images evenly across the document
                    if len(heading_indices) >= len(image_data["images"]):
                        # Choose evenly spaced heading indices
                        step = len(heading_indices) // (len(image_data["images"]) + 1)
                        if step < 1:
                            step = 1
                        
                        # Select insertion points after evenly distributed headings
                        insertion_points = []
                        for i in range(1, len(image_data["images"]) + 1):
                            idx = min(i * step, len(heading_indices) - 1)
                            heading_idx = heading_indices[idx]
                            # Insert after the paragraph following the heading
                            insertion_point = min(heading_idx + 1, len(paragraphs) - 1)
                            if insertion_point not in insertion_points:
                                insertion_points.append(insertion_point)
                    else:
                        # Not enough headings, distribute evenly throughout the document
                        total_paragraphs = len(paragraphs)
                        spacing = total_paragraphs // (len(image_data["images"]) + 1)
                        
                        # Ensure we don't insert at the very beginning
                        start_point = min(4, total_paragraphs // 10)
                        
                        insertion_points = []
                        for i in range(len(image_data["images"])):
                            # Calculate position ensuring even distribution
                            pos = start_point + (i + 1) * spacing
                            pos = min(pos, total_paragraphs - 1)  # Stay within bounds
                            
                            # Avoid inserting immediately before a heading
                            if pos < total_paragraphs - 1 and paragraphs[pos + 1].startswith('#'):
                                pos += 2  # Skip past the heading and to the content
                            
                            if pos not in insertion_points and pos < total_paragraphs:
                                insertion_points.append(pos)
                
                # Sort insertion points to maintain document structure
                insertion_points.sort()
                print(f"💡 Selected {len(insertion_points)} insertion points at paragraph indices: {insertion_points}")
                
                # Make sure we don't have more insertion points than images
                insertion_points = insertion_points[:len(image_data["images"])]
                
                # Insert images at the chosen points
                for i, insertion_idx in enumerate(insertion_points):
                    if i < len(image_data["images"]):
                        img_data = image_data["images"][i]
                        img_alt = img_data.get("alt_text") or "Image"
                        
                        if format == 'markdown':
                            img_content = f"\n\n![{img_alt}]({img_data['url']})\n\n"
                        else:  # HTML format
                            img_content = f"\n\n<img src=\"{img_data['url']}\" alt=\"{img_alt}\" style=\"max-width: 100%; height: auto;\">\n\n"
                            
                        paragraphs.insert(insertion_idx + i, img_content)  # +i to account for shifting indices
                
                # Reconstruct the document
                content = '\n\n'.join(paragraphs)
                print(f"✅ Inserted {len(insertion_points)} images throughout the document")
            else:
                # Use the original approach to replace placeholders
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
