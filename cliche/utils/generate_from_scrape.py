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

SCRAPE_OUTPUT_DIR = os.path.expanduser("~/.cliche/files/scrape")

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
def generate(topic: str, format: str, path: Optional[str], raw: bool = False):
    """Generate a document from scraped data.
    
    Examples:
        cliche generate "Machine Learning" --format markdown
        cliche generate "Python async" --format html --path ./my_doc.html
        cliche generate "React hooks" --raw  # Skip LLM processing, use direct merging
    """
    click.echo(f"📖 Using scraped data for topic: {topic}...")

    json_filename = f"{topic.replace(' ', '_').lower()}.json"
    json_path = Path(SCRAPE_OUTPUT_DIR) / json_filename
    
    if not json_path.exists():
        click.echo(f"❌ No scraped data found for '{topic}'. Run 'cliche scrape' first.")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            scraped_data = json.load(f)
    except json.JSONDecodeError:
        click.echo("❌ Error reading scraped data. The JSON file may be corrupted.")
        return
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        return

    if not scraped_data:
        click.echo("❌ No usable data found in the JSON file.")
        return

    # Generate formatted content
    formatted_content = format_scraped_data(scraped_data, topic)
    
    if not path:
        # Create a default path in the docs directory
        # Get format-specific extension
        if format == 'markdown':
            ext = '.md'
        elif format == 'html':
            ext = '.html'
        else:
            ext = f'.{format}'
            
        filename = f"{topic.replace(' ', '_').lower()}{ext}"
        output_dir = get_output_dir('docs')
        path = str(output_dir / filename)
        
    if raw:
        # Save directly without LLM processing
        with open(path, "w", encoding="utf-8") as f:
            f.write(formatted_content)
        click.echo(f"✅ Raw document saved to: {path}")
        return
    
    # Generate the final document using the write command with enhanced prompt
    prompt = f"""Generate a comprehensive technical document about '{topic}' using this structured content from multiple sources.

INSTRUCTIONS:
1. Create a cohesive, well-organized document that integrates all information from the provided sources
2. Maintain technical accuracy and include ALL technical details, code examples, and specifications
3. Organize content logically with proper headings (H1, H2, H3) to create a clear hierarchy 
4. Eliminate redundancies while preserving unique information from each source
5. Add proper transitions between sections to create a natural flow
6. Create a complete introduction that outlines the topic scope
7. Include a comprehensive conclusion summarizing key points
8. Maintain a professional, technical tone appropriate for documentation
9. Ensure ALL code examples are correctly formatted and explained
10. Preserve ALL technical terminology, details, and nuances
11. Keep ALL source references and citations intact

SOURCE MATERIALS:
{formatted_content}

Your document should be thorough and complete, using ALL relevant information from the sources.
"""
    
    click.echo("🔄 Generating document...")
    # Pass data to the LLM for a proper structured summary
    # Import here to avoid circular import
    from ..commands.write import async_write
    asyncio.run(async_write((prompt,), format, path))

if __name__ == "__main__":
    generate()
