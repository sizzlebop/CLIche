import os
import json
import asyncio
import click
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from difflib import SequenceMatcher
from collections import defaultdict
from ..utils.file import get_output_dir

SCRAPE_OUTPUT_DIR = os.path.expanduser("~/cliche/files/scrape")

def calculate_relevance_score(text: str, topic: str) -> float:
    """Calculate a relevance score between text and a topic."""
    topic_words = set(topic.lower().split())
    text_lower = text.lower()
    
    # Basic frequency counting
    word_count = 0
    for word in topic_words:
        word_count += text_lower.count(word)
    
    # Weighted by position (earlier mentions matter more)
    position_score = 0
    for word in topic_words:
        pos = text_lower.find(word)
        if pos != -1:
            # Earlier positions get higher scores
            position_score += max(0, 1.0 - (pos / min(1000, len(text_lower))))
    
    # Density score (relevant words per total length)
    density = word_count / max(1, len(text_lower.split()))
    
    # Combined score
    return (0.5 * word_count) + (0.3 * position_score) + (0.2 * density * 100)

def normalize_heading(heading: str) -> str:
    """Normalize a heading by removing markdown symbols and lowercasing."""
    return re.sub(r'^#+\s+', '', heading).lower()

def extract_headings(content: str) -> List[str]:
    """Extract all markdown headings from content."""
    return [line.strip() for line in content.split('\n') 
            if line.strip().startswith('#') and ' ' in line.strip()]

def heading_similarity(h1: str, h2: str) -> float:
    """Calculate similarity between two normalized headings."""
    return SequenceMatcher(None, normalize_heading(h1), normalize_heading(h2)).ratio()

def extract_section_content(content: str, heading: str) -> str:
    """Extract content under a specific heading."""
    lines = content.split('\n')
    heading_pattern = heading.strip().replace('#', '').strip().lower()
    
    # Find the heading
    heading_idx = -1
    for i, line in enumerate(lines):
        if line.startswith('#') and heading_pattern in line.lower():
            heading_idx = i
            break
    
    if heading_idx == -1:
        return ""
    
    # Find the next heading or end of content
    next_heading_idx = len(lines)
    for i in range(heading_idx + 1, len(lines)):
        if lines[i].startswith('#') and ' ' in lines[i]:
            next_heading_idx = i
            break
    
    # Extract content between this heading and the next
    section_content = '\n'.join(lines[heading_idx + 1:next_heading_idx]).strip()
    return section_content

def merge_and_organize_content(scraped_data: List[Dict[str, Any]], topic: str) -> str:
    """Merge and organize content from multiple sources into a coherent document.
    
    This function:
    1. Sorts content by relevance
    2. Extracts and groups similar headings
    3. Creates a structured document with table of contents
    4. Merges content from different sources under similar topics
    """
    # No data to process
    if not scraped_data:
        return f"# No content available for {topic}"
    
    # Sort sources by relevance
    sorted_items = sorted(scraped_data, 
                          key=lambda x: calculate_relevance_score(
                              x.get('main_content', '') + x.get('description', ''), 
                              topic
                          ), 
                          reverse=True)
    
    # Create document metadata and introduction
    title = f"# Comprehensive Guide: {topic}"
    intro = "## Introduction\n\n"
    
    # Use the most relevant item's description as the base for introduction
    if sorted_items:
        intro += sorted_items[0].get('description', '')
        # Add insights from other top sources
        for item in sorted_items[1:3]:  # Get description from top 3 sources
            desc = item.get('description', '')
            if desc and len(desc) > 100:  # Only substantial descriptions
                # Find unique sentences not in the intro already
                sentences = [s.strip() + '.' for s in desc.split('.') if s.strip()]
                for sentence in sentences:
                    if sentence not in intro and len(sentence) > 40:
                        intro += f"\n\n{sentence}"
    
    # Extract all headings from all sources
    heading_map = defaultdict(list)  # Maps normalized headings to (original_heading, content, source_url)
    
    for item in sorted_items:
        content = item.get('main_content', '')
        url = item.get('url', '')
        
        # Extract all headings (h2 and h3 only for better organization)
        headings = [h for h in extract_headings(content) 
                   if h.startswith('##') and not h.startswith('####')]
        
        for heading in headings:
            # Get content for this heading
            section_content = extract_section_content(content, heading)
            if section_content:
                norm_heading = normalize_heading(heading)
                heading_map[norm_heading].append((heading, section_content, url))
    
    # Group similar headings
    grouped_headings = {}
    processed_headings = set()
    
    # First, process headings in the order they appear in most relevant source
    if sorted_items:
        main_content = sorted_items[0].get('main_content', '')
        main_headings = extract_headings(main_content)
        
        # If no headings found in the main content, create a default one
        if not main_headings and main_content:
            # Create a default section for content without headings
            heading = "## Overview"
            norm_heading = normalize_heading(heading)
            processed_headings.add(norm_heading)
            
            # Add all content as one section
            combined_content = [(heading, main_content, sorted_items[0].get('url', ''))]
            grouped_headings["Overview"] = combined_content
        
        for heading in main_headings:
            norm_heading = normalize_heading(heading)
            if norm_heading in processed_headings:
                continue
                
            # Find similar headings
            similar_headings = []
            for h in heading_map:
                if h == norm_heading or h in processed_headings:
                    continue
                if heading_similarity(h, norm_heading) > 0.75:  # Similarity threshold
                    similar_headings.append(h)
            
            # Mark all similar headings as processed
            processed_headings.add(norm_heading)
            for h in similar_headings:
                processed_headings.add(h)
            
            # Collect content from original and similar headings
            combined_content = []
            combined_content.extend(heading_map[norm_heading])
            for h in similar_headings:
                combined_content.extend(heading_map[h])
            
            # Use the most common heading as the normalized one
            heading_counts = {}
            for original, _, _ in combined_content:
                clean_heading = original.replace('#', '').strip()
                heading_counts[clean_heading] = heading_counts.get(clean_heading, 0) + 1
            
            # Add fallback for when heading_counts is empty
            if not heading_counts:
                # Use the original heading if available, or a default
                if combined_content:
                    best_heading = combined_content[0][0].replace('#', '').strip()
                else:
                    best_heading = "Content Section"
            else:
                best_heading = max(heading_counts.items(), key=lambda x: x[1])[0]
            
            grouped_headings[best_heading] = combined_content
    
    # Process any remaining unprocessed headings
    for norm_heading, content_list in heading_map.items():
        if norm_heading in processed_headings:
            continue
            
        processed_headings.add(norm_heading)
        
        # Use the original heading from the most relevant source
        if content_list and content_list[0] and len(content_list[0]) > 0:
            original_heading = content_list[0][0].replace('#', '').strip()
            if not original_heading:
                original_heading = "Additional Content"
        else:
            original_heading = "Additional Content"
            
        grouped_headings[original_heading] = content_list
    
    # Build table of contents
    toc = ["## Table of Contents"]
    toc_entries = list(grouped_headings.keys())
    
    # Alphabetical sort for structured organization, keeping "Overview" first if it exists
    if "Overview" in toc_entries:
        toc_entries.remove("Overview")
        toc_entries = ["Overview"] + sorted(toc_entries)
    else:
        toc_entries = sorted(toc_entries)
    
    for i, heading in enumerate(toc_entries):
        slug = heading.lower().replace(' ', '-').replace(':', '').replace(',', '')
        toc.append(f"{i+1}. [{heading}](#{slug})")
    
    # Build content sections
    sections = []
    for heading in toc_entries:
        clean_heading = heading.lower().replace(' ', '-').replace(':', '').replace(',', '')
        sections.append(f"## {heading} {{{clean_heading}}}")
        
        # Get all content items for this heading
        content_items = grouped_headings[heading]
        
        # Sort by relevance
        content_items.sort(
            key=lambda x: calculate_relevance_score(x[1], topic),
            reverse=True
        )
        
        # Merge content from different sources
        used_sentences = set()
        merged_content = ""
        
        for _, content, url in content_items:
            # Split into paragraphs for finer merging
            paragraphs = content.split('\n\n')
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue
                    
                # Skip code blocks for deduplication (keep them all)
                if paragraph.strip().startswith('```'):
                    # Preserve code blocks without deduplication
                    if paragraph not in merged_content:
                        merged_content += "\n\n" + paragraph
                    continue
                
                # Process regular paragraphs - break into sentences
                sentences = [s.strip() + '.' for s in paragraph.replace('\n', ' ').split('.') if s.strip()]
                paragraph_to_add = ""
                
                for sentence in sentences:
                    # Skip very short sentences or those we've seen
                    if len(sentence) < 20 or sentence in used_sentences:
                        continue
                    paragraph_to_add += sentence + " "
                    used_sentences.add(sentence)
                
                if paragraph_to_add:
                    merged_content += "\n\n" + paragraph_to_add.strip()
        
        # Add the merged content
        sections.append(merged_content.strip())
        
        # Add source attribution
        unique_sources = list(set(url for _, _, url in content_items))
        if unique_sources:
            sources_text = "\n\n**Sources:**"
            for i, source in enumerate(unique_sources[:3]):  # Limit to top 3 sources per section
                sources_text += f" [[{i+1}]]({source})"
            sections.append(sources_text)
    
    # Add conclusion section if not already present
    if not any("conclusion" in h.lower() for h in grouped_headings):
        sections.append("## Conclusion")
        conclusion = f"This comprehensive guide on {topic} has covered key aspects including "
        conclusion += ", ".join([h for h in list(grouped_headings.keys())[:5]])
        conclusion += " and more. "
        conclusion += "The information presented combines insights from multiple authoritative sources to provide a thorough understanding of the subject."
        sections.append(conclusion)
    
    # Add references section
    sections.append("## References")
    unique_sources = []
    for item in sorted_items:
        url = item.get('url', '')
        title = item.get('title', 'Untitled Source')
        if url and url not in unique_sources:
            unique_sources.append(url)
            sections.append(f"- [{title}]({url})")
    
    # Combine all document parts
    return "\n\n".join([title, intro, "\n".join(toc), "\n\n".join(sections)])

def format_scraped_data(data: list, topic: str) -> str:
    """Format scraped data into a structured document."""
    # Use enhanced content organization
    return merge_and_organize_content(data, topic)

@click.command()
@click.argument("topic")
@click.option("--format", "-f", 
              type=click.Choice(["text", "markdown", "html"]), 
              default="markdown", 
              help="Output format")
@click.option("--path", "-p", 
              type=click.Path(), 
              help="Optional path to save the file")
@click.option("--raw", "-r", is_flag=True, 
              help="Generate raw merged content without LLM processing")
@click.option("--image", "-i", help='Add images related to the topic by search term', type=str)
@click.option("--image-count", default=3, help='Number of images to add', type=int)
@click.option("--image-width", default=800, help='Width of images', type=int)
def generate(topic: str, format: str, path: Optional[str], raw: bool = False,
            image: Optional[str] = None, image_count: int = 3, image_width: int = 800):
    """Generate a document from previously scraped content.
    
    This command processes content from the scrape directory for a specified topic,
    then uses an LLM to generate a well-structured document.
    
    Example: cliche generate "Python async" --format markdown
    """
    from ..core import get_llm
    from rich.console import Console
    from ..utils.unsplash import UnsplashAPI, format_image_for_markdown, format_image_for_html, get_photo_credit
    
    # Initialize console
    console = Console()
    console.print(f"[bold]Generating document for topic:[/bold] {topic}")
    
    # Load scraped data
    scrape_dir = Path(SCRAPE_OUTPUT_DIR)
    topic_filename = topic.replace(" ", "_").lower() + '.json'
    topic_file = scrape_dir / topic_filename
    topic_dir = scrape_dir / topic.replace(" ", "_").lower()
    
    # First try to load from a file with the topic name
    scraped_data = []
    if topic_file.exists() and topic_file.is_file():
        try:
            with open(topic_file, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    scraped_data = data
                else:
                    scraped_data = [data]
            console.print(f"[bold green]Found:[/bold green] Data in {topic_file}")
        except Exception as e:
            console.print(f"[bold yellow]Warning:[/bold yellow] Failed to load {topic_file}: {str(e)}")
    
    # If no data found yet, try looking in a directory
    if not scraped_data and topic_dir.exists() and topic_dir.is_dir():
        for file_path in topic_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    scraped_data.append(data)
            except Exception as e:
                console.print(f"[bold yellow]Warning:[/bold yellow] Failed to load {file_path}: {str(e)}")
        if scraped_data:
            console.print(f"[bold green]Found:[/bold green] {len(scraped_data)} data files in {topic_dir}")
    
    if not scraped_data:
        console.print(f"[bold red]Error:[/bold red] No data found for topic '{topic}'")
        console.print(f"Run [cyan]cliche scrape URL --topic \"{topic}\"[/cyan] first to collect data.")
        return

    console.print(f"[bold green]Found:[/bold green] {len(scraped_data)} data files for topic '{topic}'")
    
    # Initialize image data dictionary
    image_data = {"images": [], "credits": []}
    
    # Fetch images if requested
    if image and format in ['markdown', 'html']:
        try:
            unsplash = UnsplashAPI()
            
            # Search for images by term
            console.print(f"🔍 Searching for '{image}' images...")
            results = unsplash.search_photos(image, per_page=image_count)
            
            # Check if we have results
            photos = results.get('results', [])
            if not photos:
                console.print("❌ No images found for this search term.")
            else:
                # Download each image
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
    
    # Determine the output path
    if not path:
        # Get default output path
        output_dir = get_output_dir('write')
        filename = f"{topic.replace(' ', '_').lower()}_{format}.{format if format != 'markdown' else 'md'}"
        path = str(output_dir / filename)
        
    # Format the data
    if raw:
        # Just merge the content without LLM processing
        content = merge_and_organize_content(scraped_data, topic)
    else:
        # Use LLM to generate a well-structured document
        try:
            llm = get_llm()
            
            # Create structured content from scraped data
            raw_content = merge_and_organize_content(scraped_data, topic)
            
            # Create prompt for document generation
            doc_template = ""
            if format == 'markdown':
                doc_template = "Create a comprehensive markdown document about this topic. Use proper markdown formatting with headings, subheadings, lists, code blocks, etc. IMPORTANT: Do NOT include ```markdown or any backtick fences at the beginning or end of the document."
            elif format == 'html':
                doc_template = "Create a comprehensive HTML document about this topic. Use proper HTML structure and tags."
            else:
                doc_template = "Create a comprehensive document about this topic in plain text format."

            # Add image instructions if we have images
            if image_data["images"] and (format == 'markdown' or format == 'html'):
                doc_template += f"""

Include {len(image_data['images'])} relevant image placeholders where appropriate in the content.
IMPORTANT: Use exactly these placeholder formats:
- For markdown: ![Image Description](IMAGE_{1}) for the first image, ![Image Description](IMAGE_{2}) for the second, etc.
- For HTML: <img src="IMAGE_{1}" alt="Image Description"> for the first image, etc.
"""
            
            # Build the full prompt
            prompt = f"""
{doc_template}

TOPIC: {topic}

Based on the following content extracted from various sources, create a well-structured, comprehensive document about {topic}.
Organize the information logically, eliminate redundancies, and ensure the document flows naturally.

EXTRACTED CONTENT:
{raw_content[:15000]}  # Limiting content length to avoid token limits

Create a document that thoroughly explains {topic}, covering all important aspects and details from the provided content.
"""
            
            console.print("🧠 Generating document with AI...")
            generated_content = asyncio.run(llm.generate_response(prompt, professional_mode=True))
            
            # Process the generated content to replace image placeholders with actual images
            if format == 'markdown' or format == 'html':
                if image_data["images"]:
                    print(f"Processing {len(image_data['images'])} images for document")
                    
                    for i, img_info in enumerate(image_data["images"]):
                        # 1-indexed for placeholders
                        img_idx = i + 1
                        img_path = img_info["url"]
                        credit = img_info.get("credit", "")
                        
                        # Handle different formats
                        if format == 'markdown':
                            # When looking at the generated content, the issue is that the LLM is combining
                            # the alt text and image path incorrectly, creating malformed markdown
                            
                            # We need to find the image tag and replace the entire tag with a proper one
                            # Pattern is typically like: ![Coffee Beans]![Continuous background...]
                            
                            # First try to find patterns with IMAGE placeholder in parentheses
                            img_placeholder_patterns = [
                                r'!\[([^\]]+)\]\(IMAGE_{}\)'.format(img_idx), # ![Alt text](IMAGE_n)
                                r'!\[([^\]]+)\]!\[([^\]]+)\]\(/[^)]+\)'.format(img_idx), # ![Alt]![Description](/path)
                                r'!\[([^\]]+)\]IMAGE_{}'.format(img_idx), # ![Alt]IMAGE_n
                                r'!\[([^\]]+)\]\[IMAGE_{}\]'.format(img_idx), # ![Alt][IMAGE_n]
                                r'\(IMAGE_{}\)'.format(img_idx), # (IMAGE_n)
                                r'IMAGE_{}'.format(img_idx) # IMAGE_n plain
                            ]
                            
                            # First try these exact patterns
                            image_replaced = False
                            for pattern in img_placeholder_patterns:
                                print(f"Looking for pattern: {pattern}")
                                matches = re.finditer(pattern, generated_content)
                                for match in matches:
                                    image_replaced = True
                                    full_match = match.group(0)
                                    
                                    # Get the alt text if available, or use a default
                                    try:
                                        alt_text = match.group(1) if match.lastindex and match.lastindex >= 1 else "Coffee image"
                                    except:
                                        alt_text = "Coffee image"
                                        
                                    # Create proper markdown image
                                    proper_image = f"![{alt_text}]({img_path})"
                                    print(f"Replacing '{full_match}' with '{proper_image}'")
                                    generated_content = generated_content.replace(full_match, proper_image)
                            
                            # If no pattern matched, fall back to simple replacement
                            if not image_replaced:
                                print(f"No complex patterns matched for image {img_idx}, trying simple replacements")
                                # Try simple replacements
                                replacements = [
                                    (f"(IMAGE_{img_idx})", f"({img_path})"),
                                    (f"[IMAGE_{img_idx}]", f"[{img_path}]"),
                                    (f"IMAGE_{img_idx}", img_path)
                                ]
                                
                                for old, new in replacements:
                                    if old in generated_content:
                                        print(f"Replacing {old} with {new}")
                                        generated_content = generated_content.replace(old, new)
                                        image_replaced = True
                                        break
                                
                            if not image_replaced:
                                print(f"Unable to find any placeholder for image {img_idx}")
                        
                        elif format == 'html':
                            # Primary placeholder format: src="IMAGE_{n}"
                            primary_placeholder = f"IMAGE_{img_idx}"
                            replacement = img_path
                            
                            if primary_placeholder in generated_content:
                                print(f"Replacing {primary_placeholder} with {replacement}")
                                generated_content = generated_content.replace(primary_placeholder, replacement)
                            else:
                                print(f"Cannot find {primary_placeholder} in HTML")
                        
                    # Add image credits at the end if available
                    if any(img_info.get("credit") for img_info in image_data["images"]):
                        if format == 'markdown':
                            generated_content += "\n\n## Image Credits\n"
                            for i, img_info in enumerate(image_data["images"]):
                                if img_info.get("credit"):
                                    generated_content += f"- Image {i+1}: {img_info['credit']}\n"
                        else:  # HTML
                            credits_html = "\n<section><h2>Image Credits</h2>\n<ul>\n"
                            for i, img_info in enumerate(image_data["images"]):
                                if img_info.get("credit"):
                                    credits_html += f"<li>Image {i+1}: {img_info['credit']}</li>\n"
                            credits_html += "</ul>\n</section>"
                            
                            # Add before closing body tag if exists, otherwise append
                            if "</body>" in generated_content:
                                generated_content = generated_content.replace("</body>", f"{credits_html}\n</body>")
                            else:
                                generated_content += credits_html
            
            # Add HTML wrapper if needed
            if format == "html" and not generated_content.strip().startswith('<!DOCTYPE html>'):
                generated_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic}</title>
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
{generated_content}
</body>
</html>"""
                
        except Exception as e:
            console.print(f"[bold red]Error generating content:[/bold red] {str(e)}")
            console.print("Falling back to raw content...")
            content = merge_and_organize_content(scraped_data, topic)
    
    # Save the content
    try:
        with open(path, "w") as f:
            f.write(generated_content)
        console.print(f"[bold green]Success![/bold green] Document saved to: {path}")
        
        # Display image info if added
        if image_data["images"]:
            console.print(f"🖼️ Added {len(image_data['images'])} image(s) to the document")
            
    except Exception as e:
        console.print(f"[bold red]Error saving file:[/bold red] {str(e)}")
        
    return generated_content  # Return content in case it's used programmatically

if __name__ == "__main__":
    generate()
