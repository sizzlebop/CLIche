"""
Code generation command for CLIche.
Simplified interface for generating code in various languages.
"""
import click
import os
import asyncio
from pathlib import Path
from typing import Optional
from ..core import cli, get_llm
from ..utils.file import save_code_to_file, extract_code_blocks, get_output_dir

LANG_EXTENSIONS = {
    'python': '.py',
    'py': '.py',
    'javascript': '.js',
    'js': '.js',
    'typescript': '.ts',
    'ts': '.ts',
    'ruby': '.rb',
    'rb': '.rb',
    'rust': '.rs',
    'rs': '.rs',
    'go': '.go',
    'cpp': '.cpp',
    'c++': '.cpp',
    'csharp': '.cs',
    'cs': '.cs',
    'java': '.java',
    'php': '.php',
    'swift': '.swift',
    'kotlin': '.kt'
}

@cli.command()
@click.argument('prompt', nargs=-1, required=True)
@click.option('--lang', '-l', help='Programming language for the code', required=True)
@click.option('--path', '-p', help='Optional path to save the file', type=click.Path())
def code(prompt: tuple[str, ...], lang: str, path: Optional[str]):
    """Generate code in your chosen programming language.
    
    Examples:
        cliche code make me a game --lang python
        cliche code create a web server --lang go
        cliche code build a cli tool --lang rust
        cliche code calculator app --lang javascript
    """
    # Run async code in sync context
    asyncio.run(async_code(prompt, lang, path))

async def async_code(prompt: tuple[str, ...], lang: str, path: Optional[str]):
    """Async implementation of code command."""
    # Join the prompt parts
    full_prompt = ' '.join(prompt)
    
    # Normalize language name and get extension
    lang = lang.lower()
    ext = LANG_EXTENSIONS.get(lang, f'.{lang}')
    
    # Get default filename if path not provided
    if not path:
        # Create a filename from the first few words of the prompt
        words = full_prompt.lower().split()[:3]
        filename = '_'.join(words) + ext
        # Use the .cliche/files/code directory
        output_dir = get_output_dir('code')
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
    
    click.echo(f"🎨 Generating {lang} code for: {full_prompt}")
    
    # Get the LLM instance
    llm = get_llm()
    
    # Generate code with specific language context
    response = await llm.generate_response(
        f"Generate {lang} code for: {full_prompt}\n"
        f"Provide the code within proper markdown code blocks using triple backticks. "
        f"Include all necessary imports, dependencies, and a complete working implementation.",
        include_sys_info=False
    )
    
    # Extract code blocks
    code_blocks = extract_code_blocks(response)
    if code_blocks:
        # Use the largest code block (likely the main implementation)
        content = max(code_blocks, key=len).strip()
        
        # Save to file
        save_code_to_file(content, path)
        click.echo(f"✨ Code generated and saved to: {path}")
    else:
        click.echo("❌ No code blocks found in the response", err=True)
        return 1
    
    return 0
