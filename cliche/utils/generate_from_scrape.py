"""
Utilities for generating documents from scraped content.
"""
import os
import json
import asyncio
import click
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from difflib import SequenceMatcher
from collections import defaultdict
from ..utils.file import get_output_dir, get_docs_dir, get_unique_filename
from rich.console import Console

# Initialize console for rich output
console = Console()

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
@click.option("--summarize", "-s", is_flag=True, 
              help="Generate a summary instead of comprehensive content")
def generate(topic: str, format: str, path: Optional[str], raw: bool = False,
            image: Optional[str] = None, image_count: int = 3, image_width: int = 800,
            summarize: bool = False):
    """Generate a document from previously scraped content.
    
    This command processes content from the scrape directory for a specified topic,
    then uses an LLM to generate a well-structured document.
    
    Example: cliche generate "Python async" --format markdown
    """
    from ..core import get_llm
    from ..utils.unsplash import UnsplashAPI, format_image_for_markdown, format_image_for_html, get_photo_credit
    
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
                # Process each image
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
        output_dir = get_docs_dir('scrape')
        base_filename = f"{topic.replace(' ', '_').lower()}_{format}.{format if format != 'markdown' else 'md'}"
        # Get a unique filename
        unique_filename = get_unique_filename(output_dir, base_filename)
        path = str(output_dir / unique_filename)
        
    # Format the data
    if raw:
        # Just merge the content without LLM processing
        content = merge_and_organize_content(scraped_data, topic)
        generated_content = content  # Assign the content to generated_content
    else:
        # Use LLM to generate a well-structured document
        try:
            llm = get_llm()
            
            # Create structured content from scraped data
            raw_content = merge_and_organize_content(scraped_data, topic)
            
            if summarize:
                # Use current summarization approach
                console.print("📝 Generating summary document...")
                generated_content = generate_summary_document(llm, raw_content, topic, format, image_data)
            else:
                # Use chunking approach for comprehensive document
                console.print("📚 Generating comprehensive document with chunking approach...")
                generated_content = generate_comprehensive_document(llm, scraped_data, topic, format, image_data)
            
            # Process the generated content to replace image placeholders with actual images
            if format == 'markdown' or format == 'html':
                if image_data["images"]:
                    console.print(f"🖼️ Processing {len(image_data['images'])} images for document with AI-powered placement...")
                    generated_content = process_images_in_content(generated_content, format, image_data)
            
            # Add HTML wrapper if needed
            if format == "html" and not generated_content.strip().startswith('<!DOCTYPE html>'):
                generated_content = add_html_wrapper(generated_content, topic)
                
        except Exception as e:
            console.print(f"[bold red]Error generating content:[/bold red] {str(e)}")
            console.print("Falling back to raw content...")
            generated_content = raw_content
    
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

# Add helper functions for the new functionality

def clean_markdown_document(content):
    """Remove unwanted markdown fences and other formatting issues that could break rendering."""
    # Check if document begins with a markdown fence and remove it
    if content.strip().startswith("```") or content.strip().startswith('```markdown'):
        # Find the first triple backtick
        first_fence_pos = content.find("```")
        # Find the end of that line
        first_newline_after_fence = content.find("\n", first_fence_pos)
        if first_newline_after_fence != -1:
            # Remove everything from the start to the end of the fence line
            content = content[first_newline_after_fence+1:]
    
    # Check if document ends with a markdown fence and remove it
    if content.strip().endswith("```"):
        # Find the last triple backtick
        last_fence_pos = content.rfind("```")
        # Find the start of that line
        last_newline_before_fence = content.rfind("\n", 0, last_fence_pos)
        if last_newline_before_fence != -1:
            # Remove everything from the start of the fence line to the end
            content = content[:last_newline_before_fence]
    
    # Remove ```markdown blocks that might be in the content
    content = re.sub(r'```markdown\s*', '', content)
    content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
    
    # Remove any standalone ``` without a language specifier that might break rendering
    content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE)
    
    # Fix any duplicate heading markers (e.g., ## ## Heading)
    content = re.sub(r'(#+)\s+(#+)', r'\1', content)
    
    # Ensure proper spacing for code blocks (add newlines before and after if missing)
    content = re.sub(r'([^\n])```([a-zA-Z0-9]*)', r'\1\n```\2', content)
    content = re.sub(r'```([a-zA-Z0-9]*)([^\n])', r'```\1\n\2', content)
    
    # Ensure code blocks end properly
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)([^\n])```', r'```\1\n\2\3\n```', content, flags=re.DOTALL)
    
    # Fix code blocks with no language specifier
    content = re.sub(r'```\n', r'```text\n', content)
    
    # Add empty line after code blocks if missing
    content = re.sub(r'```\n([^`\n])', r'```\n\n\1', content)
    
    # Fix broken Python code blocks (```pytho\nn, ```py\nn, ```pyth\nn, etc.)
    content = re.sub(r'```pytho\s*\nn', r'```python\n', content)
    content = re.sub(r'```pyth\s*\nn', r'```python\n', content)
    content = re.sub(r'```py\s*\nn', r'```python\n', content)
    # Generic pattern to fix any language with escaped newlines
    content = re.sub(r'```([a-z]+)\\n', r'```\1\n', content)
    
    # Fix common incomplete language specifiers for Python
    content = re.sub(r'```pytho\s*\n', r'```python\n', content)
    content = re.sub(r'```pyth\s*\n', r'```python\n', content)
    content = re.sub(r'```py\s*\n', r'```python\n', content)
    
    # NEW: Fix specific patterns we see in the document's latter half
    
    # 1. Close code blocks that are followed by bullet points (common in the latter half)
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n\s*-\s+', r'```\1\n\2\n```\n\n- ', content, flags=re.DOTALL)
    
    # 2. Handle bullet points that immediately follow code openings (without proper separation)
    content = re.sub(r'```([a-zA-Z0-9]*)\n\s*-\s+', r'```\1\n\n- ', content, flags=re.MULTILINE)
    
    # 3. Close code blocks before "### Footnotes" and similar section markers
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n#{1,3}\s+([A-Z][a-zA-Z\s]+)', 
                    r'```\1\n\2\n```\n\n### \3', content, flags=re.DOTALL)
    
    # 4. Fix inline code inside code blocks (common in the First Steps section)
    bullet_in_code_pattern = r'```([a-zA-Z0-9]*)\n(.*?)(\n\s*-\s+[^\n]+\n)(.*?)```'
    while re.search(bullet_in_code_pattern, content, re.DOTALL):
        content = re.sub(bullet_in_code_pattern, 
                        r'```\1\n\2\n```\n\3\n```\1\n\4\n```', content, flags=re.DOTALL)
    
    # 5. Close code blocks before table of contents sections
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n(#{1,3}\s+Table of Contents)', 
                    r'```\1\n\2\n```\n\n\3', content, flags=re.DOTALL)
                    
    # 6. Close code blocks before "The output:" text (common pattern in the doc)
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n\s*The output:', 
                    r'```\1\n\2\n```\n\nThe output:', content, flags=re.DOTALL)
    
    # 7. Ensure code blocks are closed before sections starting with "Of course" (seen in example)
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n\s*Of course,', 
                    r'```\1\n\2\n```\n\nOf course,', content, flags=re.DOTALL)
    
    # 8. Close code blocks that have a mixture of code and explanatory text (common issue)
    explanatory_text_patterns = [
        r'- The ([a-zA-Z0-9_]+) (line|loop)', 
        r'- In (Python|this)', 
        r'This example', 
        r'Note that',
        r'For more information',
        r'The keyword argument'
    ]
    
    for pattern in explanatory_text_patterns:
        content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n\s*' + pattern, 
                        r'```\1\n\2\n```\n\n' + pattern, content, flags=re.DOTALL)
    
    # Fix unclosed code blocks
    # Find all opening and closing fences
    code_block_starts = re.findall(r'```[a-zA-Z0-9]*\n', content)
    code_block_ends = re.findall(r'\n```', content)
    
    # If we have more starts than ends, add missing closing fences
    if len(code_block_starts) > len(code_block_ends):
        # Find all positions of starts and ends
        start_positions = [m.start() for m in re.finditer(r'```[a-zA-Z0-9]*\n', content)]
        end_positions = [m.start() for m in re.finditer(r'\n```', content)]
        
        # Track positions that have been processed
        processed_positions = set()
        
        # Check each start position
        for i, start_pos in enumerate(start_positions):
            # Skip if this start has a matching end
            if i < len(end_positions) and start_pos < end_positions[i]:
                processed_positions.add(start_pos)
                continue
                
            # Find next heading or paragraph break after this unclosed block
            next_heading = re.search(r'\n#+\s+', content[start_pos:])
            next_para = re.search(r'\n\s*\n', content[start_pos:])
            next_bullet = re.search(r'\n\s*-\s+', content[start_pos:])
            
            # Determine position to insert closing fence
            insert_pos = start_pos
            insert_positions = []
            if next_heading:
                insert_positions.append(start_pos + next_heading.start())
            if next_para:
                insert_positions.append(start_pos + next_para.start())
            if next_bullet:
                insert_positions.append(start_pos + next_bullet.start())
                
            if insert_positions:
                insert_pos = min(insert_positions)
            else:
                insert_pos = len(content) - 1  # End of content
                
            # Insert closing fence if we haven't processed this position already
            if insert_pos not in processed_positions:
                content = content[:insert_pos] + "\n```\n" + content[insert_pos:]
                processed_positions.add(insert_pos)
    
    # Final safety check - if there are still mismatched code blocks, fix them
    # Count backtick triplets that seem to be code fence markers
    code_fence_markers = re.findall(r'```[a-zA-Z0-9]*\n|```\s*$|\n```', content)
    # If we have an odd number, we need to add one more closing fence at the end
    if len(code_fence_markers) % 2 == 1:
        # Add a closing fence at the end of the document
        content += "\n\n```\n"
        
    # Handle the case where examples and demonstrations turn into code blocks
    example_phrases = [
        r'some examples demonstrate',
        r'examples:',
        r'example:',
        r'for example:',
        r'demonstrates how',
        r'see the following example',
        r'use triple quotes',
        r'string indexing allows',
        r'Lists are',
        r'Lists can be',
        r'Consider this example',
        r'Let\'s look at an example',
        r'Here\'s an example',
        r'As an example',
        r'The following example'
    ]
    
    for phrase in example_phrases:
        # Check if the phrase is followed by a code block that's never closed properly
        pattern = f'({phrase}[^\n]*\n+```[a-zA-Z0-9]*\n)([^`]+)$'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # Add a closing fence immediately after a good break point
            example_text = match.group(2)
            # Find a good break point (paragraph break or heading)
            break_point = max(
                example_text.find('\n\n'), 
                example_text.find('\n#')
            )
            if break_point == -1:
                # If no good break point, just close after a reasonable amount of content
                break_point = min(len(example_text), 500)
            
            # Insert the closing fence
            closing_pos = match.start(2) + break_point
            content = content[:closing_pos] + "\n```\n\n" + content[closing_pos:]
    
    # NEW: Additional final cleaning steps
    
    # 1. Remove any empty code blocks that might have been created during fixes
    content = re.sub(r'```[a-zA-Z0-9]*\n\s*```\n', '', content)
    
    # 2. Fix consecutive code blocks without text in between
    content = re.sub(r'```\n\n```([a-zA-Z0-9]*)', r'```\1', content)
    
    # 3. Ensure a blank line after every code block closing
    content = re.sub(r'```\n([^`\n])', r'```\n\n\1', content)
    
    # 4. Remove trailing whitespace at the end of lines
    content = re.sub(r' +$', '', content, flags=re.MULTILINE)
    
    # 5. Fix spaces around code backticks
    content = re.sub(r'(\S)```', r'\1\n```', content)
    
    # Additional fix for orphaned code blocks by scanning the whole document
    # Find all code block openings
    code_block_starts = list(re.finditer(r'```[a-zA-Z0-9]*\n', content))
    
    # For each start, check if it has a matching closing fence
    for i, start_match in enumerate(code_block_starts):
        start_pos = start_match.end()
        # Find the next code fence (opening or closing)
        next_fence = re.search(r'```', content[start_pos:])
        
        # If no next fence found or it's another opening fence, we need to close this block
        if not next_fence or content[start_pos + next_fence.start() - 3:start_pos + next_fence.start()].strip() == '':
            # Find a good place to close - next heading or paragraph break
            next_heading = re.search(r'\n#+\s+', content[start_pos:])
            next_para = re.search(r'\n\s*\n', content[start_pos:])
            next_bullet = re.search(r'\n\s*-\s+', content[start_pos:])
            
            # Determine position to insert closing fence
            insert_positions = []
            if next_heading: insert_positions.append(start_pos + next_heading.start())
            if next_para: insert_positions.append(start_pos + next_para.start())
            if next_bullet: insert_positions.append(start_pos + next_bullet.start())
            
            if insert_positions:
                insert_pos = min(insert_positions)
            else:
                # If no good break points, insert fence at the end of the document
                insert_pos = len(content)
            
            # Add closing fence
            content = content[:insert_pos] + "\n```\n\n" + content[insert_pos:]
    
    # Final scan - ensure that all ```python are followed by a matching ``` closure
    # This handles code blocks in sections like "### 3.1.5 Lists" that don't get caught by other patterns
    sections = re.split(r'^#{2,}\s+.*$', content, flags=re.MULTILINE)
    result_parts = []
    
    # Process the content in sections
    heading_matches = re.finditer(r'^(#{2,}\s+.*?)$', content, flags=re.MULTILINE)
    headings = [m.group(1) for m in heading_matches]
    
    # Handle the case where the first section doesn't have a heading
    if not content.lstrip().startswith('#'):
        first_heading_pos = content.find('#')
        if first_heading_pos > 0:
            sections = [content[:first_heading_pos]] + sections
            headings = [""] + headings
    
    for i, section in enumerate(sections):
        if i < len(headings):
            current_heading = headings[i]
        else:
            current_heading = ""
            
        # Count code fence markers in this section
        fence_markers = re.findall(r'```', section)
        
        # If odd number of markers, add a closing fence
        if len(fence_markers) % 2 == 1:
            # Find the last code block start
            last_start = section.rfind("```")
            if last_start != -1:
                # Check if this is actually an opening fence
                next_line_start = section[last_start:].find('\n')
                if next_line_start != -1 and last_start + next_line_start + 1 < len(section):
                    # This is likely an opening fence if there's text after ```
                    # Add a closing fence at the end of the section
                    section += "\n```\n"
        
        # Add heading and processed section to result
        if current_heading:
            result_parts.append(current_heading)
        result_parts.append(section)
    
    # Combine processed sections
    content = ''.join(result_parts)
    
    # TOC entries that use bold formatting instead of links
    toc_section_match = re.search(r'## Table of Contents\s+((?:.+\n)+)', content, re.IGNORECASE)
    if toc_section_match:
        toc_section = toc_section_match.group(1)
        # Find entries that use bold formatting instead of links
        # Pattern: digit. **Some Text** (with optional spaces)
        bold_entries = re.findall(r'(\d+\.\s+\*\*([^*]+)\*\*)', toc_section)
        
        # Replace each bold entry with a proper link
        for full_match, text in bold_entries:
            # Create a proper anchor link: lowercase with hyphens instead of spaces
            anchor = text.strip().lower().replace(' ', '-')
            # Create the proper markdown link
            link_format = f'{full_match[0:full_match.find("*")]}[{text.strip()}](#{anchor})'
            # Replace in the content
            content = content.replace(full_match, link_format)
    
    # VS Code compatible heading ID generation and link fixing
    
    # 1. Extract all headings and create properly formatted IDs based on GitHub/VS Code approach
    headings = re.findall(r'^(#+)\s+(.*?)$', content, re.MULTILINE)
    heading_map = {}
    
    for level, heading_text in headings:
        clean_text = heading_text.strip()
        
        # Remove any markdown formatting from heading text (bold, italic, etc.)
        # This is important because VS Code ignores formatting in ID generation
        clean_text_no_format = re.sub(r'(\*\*|\*|__|_|~~)', '', clean_text)
        
        # Generate VS Code compatible IDs:
        # - Lowercase
        # - Replace spaces with hyphens
        # - Remove all special characters except hyphens
        # - Handle duplicates (not implemented here but VS Code would add numbers)
        std_id = re.sub(r'[^\w\- ]', '', clean_text_no_format.lower()).strip().replace(' ', '-')
        
        # Store both the raw heading and the cleaned version
        heading_map[clean_text] = std_id
        heading_map[clean_text_no_format] = std_id  # Also map the version without formatting
    
    # 2. Find the Table of Contents section more precisely
    toc_start = content.find("## Table of Contents")
    if toc_start != -1:
        # Find the next heading (## or #) after TOC to determine TOC end
        next_heading_match = re.search(r'^#{1,2}[^#]', content[toc_start+20:], re.MULTILINE)
        if next_heading_match:
            toc_end = toc_start + 20 + next_heading_match.start()
            toc_section = content[toc_start:toc_end]
        else:
            # If no next heading, look for a reasonable delimiter (multiple newlines)
            next_para_match = re.search(r'\n\n+', content[toc_start+20:])
            if next_para_match:
                toc_end = toc_start + 20 + next_para_match.start()
                toc_section = content[toc_start:toc_end]
            else:
                # Last resort - take up to 20 lines after TOC heading
                toc_section = '\n'.join(content[toc_start:].split('\n')[:20])
        
        # 3. Find and fix all TOC links 
        link_pattern = r'\[(.*?)\]\((#.*?)\)'
        toc_links = re.findall(link_pattern, toc_section)
        
        for link_text, link_target in toc_links:
            # Get actual heading text that should match this link
            clean_link_text = link_text.strip()
            
            # Try to find a match - first with exact text, then with formatting removed
            if clean_link_text in heading_map:
                target_id = heading_map[clean_link_text]
            else:
                # Remove any markdown formatting and try again
                clean_link_no_format = re.sub(r'(\*\*|\*|__|_|~~)', '', clean_link_text)
                if clean_link_no_format in heading_map:
                    target_id = heading_map[clean_link_no_format]
                else:
                    # As a fallback, try to generate the ID directly
                    target_id = re.sub(r'[^\w\- ]', '', clean_link_text.lower()).strip().replace(' ', '-')
            
            # Create correct VS Code compatible link
            new_target = f"#{target_id}"
            
            # Replace only in TOC section to avoid changing content links
            old_link = f"[{link_text}]{link_target}"
            new_link = f"[{link_text}]({new_target})"
            
            # Find exact position of old link in content
            pos = content.find(old_link)
            if pos != -1 and pos < toc_end:
                content = content[:pos] + new_link + content[pos+len(old_link):]
    
    # Ensure any nested section lists in TOC also have proper links
    nested_links = re.findall(r'[ \t]+- \[(.*?)\]\((#.*?)\)', content)
    for link_text, link_target in nested_links:
        clean_link_text = link_text.strip()
        
        # Similar logic as above for finding the correct target ID
        if clean_link_text in heading_map:
            target_id = heading_map[clean_link_text]
        else:
            clean_link_no_format = re.sub(r'(\*\*|\*|__|_|~~)', '', clean_link_text)
            if clean_link_no_format in heading_map:
                target_id = heading_map[clean_link_no_format]
            else:
                target_id = re.sub(r'[^\w\- ]', '', clean_link_text.lower()).strip().replace(' ', '-')
        
        new_target = f"#{target_id}"
        old_link = f"[{link_text}]{link_target}"
        new_link = f"[{link_text}]({new_target})"
        content = content.replace(old_link, new_link)
    
    # Clean up any problematic markdown formatting and also handle HTML content
    if format == 'markdown':
        content = clean_markdown_document(content)
    elif format == 'html':
        # Remove any stray markdown code fences from the HTML content
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
    
    return content

def generate_summary_document(llm, raw_content, topic, format, image_data):
    """Generate a summary document using the LLM."""
    # Create prompt for document generation
    doc_template = ""
    if format == 'markdown':
        doc_template = """Create a comprehensive markdown document about this topic. Use proper markdown formatting with headings, subheadings, lists, and code blocks. 

For code blocks, follow these strict formatting rules:
1. ALWAYS use three backticks (```) to open AND close every code block
2. ALWAYS specify a language (e.g., ```python, ```bash) for syntax highlighting
3. ALWAYS include a blank line before AND after each code block
4. NEVER have text directly adjacent to the opening or closing fence
5. ALWAYS close code blocks before starting new paragraphs or sections
6. When showing examples with code, ALWAYS close the code block before continuing with explanations

EXTREMELY IMPORTANT: Do NOT include ```markdown or ```anything at the beginning of the document. 
EXTREMELY IMPORTANT: Do NOT include ``` at the end of the document.
EXTREMELY IMPORTANT: Only use triple backticks for actual code blocks within the document."""
    elif format == 'html':
        doc_template = """Create a comprehensive HTML document about this topic. The ENTIRE content must use proper HTML tags, not Markdown syntax.

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

Every single piece of content must be enclosed in appropriate HTML tags. Do not mix HTML and Markdown syntax anywhere."""
    else:
        doc_template = "Create a comprehensive document about this topic in plain text format."

    # Add image instructions if we have images
    if image_data["images"] and (format == 'markdown' or format == 'html'):
        doc_template += add_image_instructions(image_data)
    
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
    
    response = asyncio.run(llm.generate_response(prompt, professional_mode=True))
    
    # Clean up any problematic markdown formatting
    if format == 'markdown':
        response = clean_markdown_document(response)
    
    return response

def generate_comprehensive_document(llm, scraped_data, topic, format, image_data):
    """Generate a comprehensive document using a chunking approach."""
    # First, extract major sections from the content
    sections = extract_major_sections(scraped_data)
    
    # Generate the document title and introduction
    intro_template = f"""
Write a title and introduction for a comprehensive document about {topic}.
The document will cover the following sections:
{', '.join(sections.keys())}

Your response should only include:
1. A main title (using # for markdown)
2. A brief introduction paragraph
3. A table of contents with the sections listed

For the table of contents, use proper markdown link format for ALL entries:
[Section Name](#section-name) - where section-name is the section name in lowercase with spaces replaced by hyphens.

Example format:
## Table of Contents
1. [Introduction](#introduction)
2. [Basic Commands](#basic-commands)
3. [Advanced Usage](#advanced-usage)

EXTREMELY IMPORTANT: Do NOT use bold formatting (**text**) for any table of contents entries, always use links.
EXTREMELY IMPORTANT: Do NOT include ```markdown or ```anything at the beginning of your response. 
EXTREMELY IMPORTANT: Do NOT include ``` at the end of your response.
No other content is needed as the sections will be filled in separately.
"""
    
    intro_response = asyncio.run(llm.generate_response(intro_template, professional_mode=True))
    
    # Process each section separately
    processed_sections = {}
    total_sections = len(sections)
    current_section = 0
    
    for section_title, section_content in sections.items():
        current_section += 1
        console.print(f"Processing section {current_section}/{total_sections}: {section_title}")
        
        # Use a consistent template that avoids triple backtick code blocks for all sections
        section_template = f"""
You are processing just one section of a larger document about {topic}.
This section is titled: "{section_title}"

Format this section content with proper headings, paragraphs, lists, and formatting.
Preserve ALL technical details, examples, and explanations.
DO NOT SUMMARIZE OR OMIT CONTENT - include everything from the source material.
Start the section with a level 2 heading (##).

IMPORTANT: For code examples, use indentation (4 spaces at the beginning of each line) instead of triple backticks.
Example of proper code formatting with indentation:

    # This is Python code
    def example_function():
        return "This is properly formatted"

For inline code, use single backticks like `variable_name` or `function()`.

EXTREMELY IMPORTANT: 
- DO NOT use triple backticks (```) for code blocks anywhere in your response
- Format all code examples with 4-space indentation only
- Keep code examples separate from explanatory text with blank lines
- Use bold text (**text**) for emphasis instead of headings within the section

SECTION CONTENT:
{section_content}
"""
        
        # Process this section with the LLM
        try:
            console.print(f"Processing section {current_section} with indented code blocks...")
            section_response = asyncio.run(llm.generate_response(section_template, professional_mode=True))
            processed_sections[section_title] = section_response
        except Exception as e:
            console.print(f"Error processing section {current_section}: {str(e)}")
            # For problematic sections, fall back to the raw content
            console.print(f"Falling back to raw content for section {current_section}")
            processed_sections[section_title] = f"## {section_title}\n\n{section_content}"
    
    # Combine all parts into one document
    document = intro_response + "\n\n"
    
    # Add each processed section
    for section_title, section_content in processed_sections.items():
        document += section_content + "\n\n"
    
    # Add conclusion
    conclusion_template = f"""
Write a brief conclusion for a comprehensive document about {topic}.
The conclusion should be no more than 1-2 paragraphs and should wrap up the key points.
Start with a level 2 heading (## Conclusion).

IMPORTANT: 
- Do NOT include ```markdown or any backtick fences around your response.
- Do NOT use triple backticks (```) for code blocks - use 4-space indentation instead.
"""
    
    conclusion_response = asyncio.run(llm.generate_response(conclusion_template, professional_mode=True))
    document += conclusion_response
    
    # Replace any remaining triple backtick code blocks with indented code
    document = replace_backticks_with_indentation(document)
    
    # Use simplified cleaning for any other markdown formatting issues
    document = simplified_clean_markdown(document)
    
    return document

# Add a new function to replace any remaining triple backtick code blocks with indented code
def replace_backticks_with_indentation(content):
    """Replace any triple backtick code blocks with 4-space indented code."""
    # Find all code blocks
    code_block_pattern = re.compile(r'```(?:[a-zA-Z0-9]*)\n(.*?)\n```', re.DOTALL)
    
    # Function to replace each match with indented code
    def indent_code(match):
        code = match.group(1)
        # Split into lines, indent each line, and rejoin
        indented_lines = []
        for line in code.split('\n'):
            indented_lines.append('    ' + line)
        return '\n' + '\n'.join(indented_lines) + '\n'
    
    # Replace all code blocks
    content = code_block_pattern.sub(indent_code, content)
    
    return content

# Add a simplified version of clean_markdown_document that's less aggressive about code blocks
def simplified_clean_markdown(content):
    """A simplified version of clean_markdown_document that does basic cleanup without complex code block fixing."""
    # Check if document begins with a markdown fence and remove it
    if content.strip().startswith("```") or content.strip().startswith('```markdown'):
        first_fence_pos = content.find("```")
        first_newline_after_fence = content.find("\n", first_fence_pos)
        if first_newline_after_fence != -1:
            content = content[first_newline_after_fence+1:]
    
    # Check if document ends with a markdown fence and remove it
    if content.strip().endswith("```"):
        last_fence_pos = content.rfind("```")
        last_newline_before_fence = content.rfind("\n", 0, last_fence_pos)
        if last_newline_before_fence != -1:
            content = content[:last_newline_before_fence]
    
    # Remove ```markdown blocks that might be in the content
    content = re.sub(r'```markdown\s*', '', content)
    content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
    
    # Fix any duplicate heading markers (e.g., ## ## Heading)
    content = re.sub(r'(#+)\s+(#+)', r'\1', content)
    
    # Add a simple final check for unclosed code blocks
    code_block_starts = re.findall(r'```[a-zA-Z0-9]*\n', content)
    code_block_ends = re.findall(r'\n```', content)
    
    # If we have more starts than ends, add a closing fence at the end
    if len(code_block_starts) > len(code_block_ends):
        content += "\n\n```\n"
    
    return content

def extract_major_sections(scraped_data):
    """Extract major sections from the scraped data."""
    sections = {}
    
    console.print(f"Extracting sections from {len(scraped_data)} data sources...")
    
    for item_idx, item in enumerate(scraped_data):
        content = item.get('main_content', '')
        
        console.print(f"Processing source {item_idx+1}, content length: {len(content)} chars")
        
        # Check if content uses \n escape sequences instead of actual newlines
        if '\\n' in content and '\n' not in content[:1000]:
            # Content likely has escape sequences - split by \n and clean up
            console.print("Detected escaped newlines format, converting...")
            lines = content.replace('\\n', '\n').split('\n')
        else:
            # Regular content with actual newlines
            lines = content.split('\n')
        
        # Try to identify section markers
        section_markers = []
        for i, line in enumerate(lines):
            # Check for potential section headings (capitalized words with no punctuation)
            if re.match(r'^[A-Z][A-Za-z0-9 ]+$', line.strip()) and len(line.strip()) < 50:
                section_markers.append((i, line.strip()))
        
        # If we found potential sections, use them
        if len(section_markers) >= 3:  # Need at least a few sections to be valid
            console.print(f"Found {len(section_markers)} potential section markers")
            
            # Process content by sections
            current_section = "Overview"
            section_content = ""
            section_count = 0
            
            for i in range(len(section_markers)):
                # Current section marker
                _, section_title = section_markers[i]
                
                # Get content until next section marker
                start_idx = section_markers[i][0]
                end_idx = section_markers[i+1][0] if i < len(section_markers) - 1 else len(lines)
                
                # Get content for this section
                section_text = "\n".join(lines[start_idx:end_idx])
                
                # Start with a proper markdown heading
                section_content = f"## {section_title}\n\n{section_text}"
                
                # Add to sections dict
                if section_title in sections:
                    sections[section_title] += "\n\n" + section_content
                else:
                    sections[section_title] = section_content
                    section_count += 1
            
            console.print(f"Extracted {section_count} sections using content markers")
        
        else:
            # Fall back to searching for ## headings or try to split by blank lines
            console.print("No clear section markers found, looking for markdown headings...")
            current_section = "Overview"
            section_content = ""
            section_count = 0
            
            # First try to find markdown-style headings
            has_markdown_headings = False
            
            for line in lines:
                # Check if it's a section heading (## level, but not ### or deeper)
                if line.startswith('##') and not line.startswith('###'):
                    has_markdown_headings = True
                    # Save the previous section
                    if section_content:
                        if current_section in sections:
                            sections[current_section] += "\n\n" + section_content
                        else:
                            sections[current_section] = section_content
                            section_count += 1
                    
                    # Start a new section
                    current_section = line.strip('# ')
                    section_content = line + "\n"
                else:
                    section_content += line + "\n"
            
            # If no markdown headings found, try to create sections from content
            if not has_markdown_headings:
                console.print("No markdown headings found, creating artificial sections...")
                
                # Create artificial sections based on content length
                paragraph_groups = []
                current_group = []
                
                for line in lines:
                    if not line.strip():
                        if current_group:  # If we have a non-empty group
                            paragraph_groups.append("\n".join(current_group))
                            current_group = []
                    else:
                        current_group.append(line)
                
                # Add the last group if it exists
                if current_group:
                    paragraph_groups.append("\n".join(current_group))
                
                # Create artificial sections based on content (try to find logical breaks)
                if paragraph_groups:
                    # Create intro section
                    sections["Introduction"] = f"## Introduction\n\n{paragraph_groups[0]}"
                    
                    # Create main content sections
                    chunks = []
                    current_chunk = []
                    chunk_length = 0
                    
                    # Target each section to be roughly 2000-3000 chars
                    for i, group in enumerate(paragraph_groups[1:], 1):
                        current_chunk.append(group)
                        chunk_length += len(group)
                        
                        # Create a new chunk if we reach target size or are at the end
                        if chunk_length > 3000 or i == len(paragraph_groups) - 1:
                            chunks.append("\n\n".join(current_chunk))
                            current_chunk = []
                            chunk_length = 0
                    
                    # Add the chunks as sections
                    for i, chunk in enumerate(chunks, 1):
                        section_name = f"Section {i}"
                        sections[section_name] = f"## {section_name}\n\n{chunk}"
                    
                    console.print(f"Created {len(chunks) + 1} artificial sections from content")
            
            # Save the last section if using markdown headings
            if has_markdown_headings and section_content:
                if current_section in sections:
                    sections[current_section] += "\n\n" + section_content
                else:
                    sections[current_section] = section_content
                    section_count += 1
                
                console.print(f"Extracted {section_count} sections using markdown headings")
    
    # Ensure we have an Overview section if it's missing
    if "Overview" not in sections and "Introduction" not in sections and scraped_data:
        # Create an overview from the descriptions
        overview = "## Overview\n\n"
        for item in scraped_data:
            description = item.get('description', '')
            if description:
                overview += description + "\n\n"
        
        if len(overview) > 20:  # Only add if we have substantial content
            sections["Overview"] = overview
    
    console.print(f"Total sections extracted: {len(sections)}")
    for section_name, content in sections.items():
        console.print(f"- Section '{section_name}': {len(content)} chars")
    
    return sections

def add_image_instructions(image_data):
    """Add instructions for image placement."""
    # Simplified to remove extensive placeholder instructions
    return f"""

IMPORTANT: Do NOT start your response with ```markdown or any code fences. 
Do NOT enclose your entire response in code fences.
"""

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

def process_images_in_content(content, format, image_data):
    """Process image placeholders in the content."""
    if not image_data["images"]:
        return content
    
    # Check if any IMAGE_ string appears at all in the document
    all_image_indicators = len(re.findall(r'IMAGE_\d+', content))
    
    # If no placeholders found, let's use LLM to suggest image placement
    if all_image_indicators == 0:
        print("💡 Using AI-powered image placement to find optimal locations...")
        
        # Split content into paragraphs for placement
        paragraphs = content.split('\n\n')
        
        # Create async function to run our image placement suggestions
        async def run_image_placement(content, topic, format, image_count):
            from ..core import get_llm
            llm = get_llm()
            return await get_image_placement_suggestions(
                llm=llm,
                document_content=content,
                image_count=image_count,
                topic=topic,
                format=format
            )
        
        # Run the async function to get suggestions
        import asyncio
        try:
            # Get a topic from the content if not provided
            topic = "document"
            title_match = re.search(r'^# (.+)', content, re.MULTILINE)
            if title_match:
                topic = title_match.group(1)
                
            # Use asyncio.run to execute the async function
            insertion_points = asyncio.run(run_image_placement(
                content=content,
                topic=topic,
                format=format,
                image_count=len(image_data["images"])
            ))
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
        return content
        
    # Process placeholders in the original approach
    for i, img_info in enumerate(image_data["images"]):
        # 1-indexed for placeholders
        img_idx = i + 1
        img_path = img_info["url"]
        
        # Handle different formats
        if format == 'markdown':
            # Try to find patterns with IMAGE placeholder
            img_placeholder_patterns = [
                r'!\[([^\]]+)\]\(IMAGE_{}\)'.format(img_idx),
                r'!\[([^\]]+)\]!\[([^\]]+)\]\(/[^)]+\)'.format(img_idx),
                r'!\[([^\]]+)\]IMAGE_{}'.format(img_idx),
                r'!\[([^\]]+)\]\[IMAGE_{}\]'.format(img_idx),
                r'\(IMAGE_{}\)'.format(img_idx),
                r'IMAGE_{}'.format(img_idx)
            ]
            
            # Try these patterns
            image_replaced = False
            for pattern in img_placeholder_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    image_replaced = True
                    full_match = match.group(0)
                    
                    # Get the alt text if available
                    try:
                        alt_text = match.group(1) if match.lastindex and match.lastindex >= 1 else "Image"
                    except:
                        alt_text = "Image"
                        
                    # Create proper markdown image
                    proper_image = f"![{alt_text}]({img_path})"
                    content = content.replace(full_match, proper_image)
            
            # If no pattern matched, try simple replacements
            if not image_replaced:
                # Try simple replacements
                replacements = [
                    (f"(IMAGE_{img_idx})", f"({img_path})"),
                    (f"[IMAGE_{img_idx}]", f"[{img_path}]"),
                    (f"IMAGE_{img_idx}", img_path)
                ]
                
                for old, new in replacements:
                    if old in content:
                        content = content.replace(old, new)
                        image_replaced = True
                        break
        
        elif format == 'html':
            # Primary placeholder format: src="IMAGE_{n}"
            primary_placeholder = f"IMAGE_{img_idx}"
            replacement = img_path
            
            if primary_placeholder in content:
                content = content.replace(primary_placeholder, replacement)
            else:
                # Try to find <img src="IMAGE_n" patterns
                img_html_pattern = r'<img[^>]*src=["\'](IMAGE_{})["\'][^>]*>'.format(img_idx)
                matches = re.finditer(img_html_pattern, content)
                for match in matches:
                    full_match = match.group(0)
                    new_img_tag = full_match.replace(f'src="{primary_placeholder}"', f'src="{img_path}"')
                    content = content.replace(full_match, new_img_tag)
    
    # Add image credits at the end
    if image_data["credits"]:
        if format == 'markdown':
            content += "\n\n## Image Credits\n"
            for i, credit in enumerate(image_data["credits"]):
                content += f"- {credit}\n"
        else:  # HTML
            credits_html = "\n<section><h2>Image Credits</h2>\n<ul>\n"
            for i, credit in enumerate(image_data["credits"]):
                credits_html += f"<li>{credit}</li>\n"
            credits_html += "</ul>\n</section>"
            
            # Add before closing body tag if exists, otherwise append
            if "</body>" in content:
                content = content.replace("</body>", f"{credits_html}\n</body>")
            else:
                content += credits_html
    
    return content

def add_html_wrapper(content, title):
    """Add HTML wrapper to the content."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
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

if __name__ == "__main__":
    generate()
