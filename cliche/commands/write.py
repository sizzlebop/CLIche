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
@click.option('--type', '-t', type=click.Choice(['text', 'markdown', 'html']), default='text',
              help='Type of content to generate')
@click.option('--path', '-p', help='Optional path to save the file', type=click.Path())
def write(prompt: tuple[str, ...], type: str, path: Optional[str]):
    """Generate text content in various formats.
    
    Examples:
        cliche write a tutorial on docker --type markdown
        cliche write a blog post about AI --type html
        cliche write a project readme --type markdown
        cliche write meeting notes from today
    """
    # Run async code in sync context
    asyncio.run(async_write(prompt, type, path))

async def async_write(prompt: tuple[str, ...], type: str, path: Optional[str]):
    """Async implementation of write command."""
    # Join the prompt parts
    full_prompt = ' '.join(prompt)
    
    # Determine file extension
    ext = {
        'text': '.txt',
        'markdown': '.md',
        'html': '.html'
    }[type]
    
    # Get default filename if path not provided
    if not path:
        # Create a filename from the first few words of the prompt
        words = full_prompt.lower().split()[:3]
        filename = '_'.join(words) + ext
        # Use the .cliche/files/write directory
        output_dir = get_output_dir('write')
        path = str(output_dir / filename)
    elif os.path.isdir(path):
        # If path is a directory, append a filename
        words = full_prompt.lower().split()[:3]
        filename = '_'.join(words) + ext
        path = os.path.join(path, filename)
    elif not path.endswith(ext):
        # Ensure correct extension
        path += ext
    
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    
    click.echo(f"✍️ Generating {type} content for: {full_prompt}")
    
    # Get the LLM instance
    llm = get_llm()
    
    # Generate content with specific format context
    format_prompts = {
        'markdown': (
            "Write this in markdown format with proper headings, lists, code blocks, and formatting.\n"
            "Use # for main heading, ## for subheadings, - for lists, ``` for code blocks.\n"
            "Include emojis where appropriate. Make it engaging and well-structured.\n"
            "Topic:"
        ),
        'html': (
            "Write this as a properly formatted HTML document with appropriate tags and structure.\n"
            "Include <!DOCTYPE html>, <html>, <head>, <body> tags, and proper indentation.\n"
            "Make it modern and well-structured.\n"
            "Topic:"
        ),
        'text': "Write this as plain text with clear paragraphs and structure. Topic:"
    }
    
    response = await llm.generate_response(
        f"{format_prompts[type]} {full_prompt}",
        include_sys_info=False
    )
    
    # For HTML, ensure we have proper structure
    if type == 'html' and not response.strip().startswith('<!DOCTYPE html>'):
        response = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{full_prompt}</title>
</head>
<body>
{response}
</body>
</html>"""
    
    # Save to file
    save_text_to_file(response, path)
    click.echo(f"✨ Content generated and saved to: {path}")
    
    # For markdown, show preview
    if type == 'markdown':
        click.echo("\n📝 Preview of the first few lines:")
        preview_lines = response.split('\n')[:5]
        click.echo('\n'.join(preview_lines))
        click.echo("...")
    
    return 0
