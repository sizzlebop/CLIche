import os
import json
import asyncio
import click
from pathlib import Path
from typing import Optional
from ..utils.file import get_output_dir

SCRAPE_OUTPUT_DIR = os.path.expanduser("~/.cliche/files/scrape")

def format_scraped_data(data: list) -> str:
    """Format scraped data into a structured document."""
    sections = []
    
    for item in data:
        title = item.get('title', 'Untitled')
        url = item.get('url', 'N/A')
        description = item.get('description', 'No description available.')
        content = item.get('main_content', 'No content available.')
        
        section = f"""
# {title}

**Source:** {url}

## Summary
{description}

## Content
{content}

---
"""
        sections.append(section)
    
    return '\n'.join(sections)

@click.command()
@click.argument("topic")
@click.option("--format", "-f", 
              type=click.Choice(["text", "markdown", "html"]), 
              default="markdown", 
              help="Output format")
@click.option("--path", "-p", 
              type=click.Path(), 
              help="Optional path to save the file")
def generate(topic: str, format: str, path: Optional[str]):
    """Generate a document from scraped data.
    
    Examples:
        cliche generate "Machine Learning" --format markdown
        cliche generate "Python async" --format html --path ./my_doc.html
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

    # Format the scraped data into a structured document
    formatted_content = format_scraped_data(scraped_data)
    
    # Generate the final document using the write command
    prompt = f"Generate a comprehensive document about {topic} using this structured content as source material:\n\n{formatted_content}"
    
    click.echo("🔄 Generating document...")
    # Pass data to the LLM for a proper structured summary
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
        
    # Import here to avoid circular import
    from ..commands.write import async_write
    asyncio.run(async_write((prompt,), format, path))

if __name__ == "__main__":
    generate()
