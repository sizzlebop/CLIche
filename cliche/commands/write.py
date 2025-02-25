"""
Text generation command for CLIche.
Simplified interface for generating text content in various formats.
"""
import click
import os
import asyncio
from pathlib import Path
from typing import Optional
from ..core import cli, get_llm
from ..utils.file import save_text_to_file, get_output_dir

@cli.command()
@click.argument('prompt', nargs=-1, required=True)
@click.option('--format', '-f', type=click.Choice(['text', 'markdown', 'html']), default='text',
              help='Type of content to generate')
@click.option('--path', '-p', help='Optional path to save the file', type=click.Path())
def write(prompt: tuple[str, ...], format: str, path: Optional[str]):
    """Generate text content in various formats.
    
    Examples:
        cliche write a tutorial on docker --type markdown
        cliche write a blog post about AI --type html
        cliche write a project readme --type markdown
        cliche write meeting notes from today
    """
    # Run async code in sync context
    asyncio.run(async_write(prompt, format, path))

async def async_write(prompt: tuple[str, ...], format: str, path: Optional[str]):
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
        output_dir = get_output_dir('docs')
        path = str(output_dir / filename)
    
    # Add format-specific instructions
    format_instructions = {
        'text': 'Write this as a plain text document without any special formatting.',
        'markdown': 'Write this as a markdown document with proper formatting. Use markdown features like headings, lists, code blocks, bold, italic, and links as appropriate. Format your response using rich markdown syntax.',
        'html': 'Write this as an HTML document with proper tags and structure.'
    }[format]
    
    full_prompt = f"{format_instructions}\n\n{full_prompt}"
    
    # Get the LLM instance
    llm = get_llm()
    
    click.echo("🔄 Generating content...")
    
    try:
        # Generate content - use professional mode for document generation
        content = await llm.generate_response(full_prompt, professional_mode=True)
        
        if format == 'html' and not content.strip().startswith('<!DOCTYPE html>'):
            content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Content</title>
</head>
<body>
{content}
</body>
</html>"""
        
        # Save to file
        save_text_to_file(content, path)
        click.echo(f"✅ Content saved to: {path}")
        
    except AttributeError as e:
        click.echo("❌ Error: Provider not properly configured")
        return
    except Exception as e:
        click.echo(f"❌ Error generating content: {str(e)}")
