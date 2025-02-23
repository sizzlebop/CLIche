"""
File management commands
"""
import click
import os
import fnmatch
import shutil
import stat
import asyncio
import re
from pathlib import Path
from typing import Optional, List

@click.command()
@click.argument('source')
@click.argument('target')
@click.option('--force', '-f', is_flag=True, help='Force rename even if target exists')
def rename(source: str, target: str, force: bool) -> None:
    """Rename a file or directory."""
    try:
        source_path = Path(source)
        target_path = Path(target)
        
        if not source_path.exists():
            click.echo(f"Source '{source}' does not exist")
            return
            
        if target_path.exists() and not force:
            click.echo(f"Target '{target}' already exists. Use --force to overwrite")
            return
            
        # Create parent directories if they don't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle read-only files
        if source_path.is_file() and not os.access(str(source_path), os.W_OK):
            os.chmod(str(source_path), stat.S_IWRITE)
            
        if target_path.exists() and force:
            if target_path.is_file():
                os.chmod(str(target_path), stat.S_IWRITE)
            target_path.unlink()
            
        source_path.rename(target_path)
        click.echo(f"Renamed '{source}' to '{target}'")
        
    except PermissionError:
        click.echo(f"Permission denied: Unable to rename '{source}' to '{target}'")
    except OSError as e:
        click.echo(f"Error renaming file: {str(e)}")

@click.command()
@click.option('--name', '-n', help='File name pattern (e.g., *.txt)')
@click.option('--type', '-t', 'filetype', help='File type (e.g., pdf, jpg)')
@click.option('--path', '-p', type=click.Path(exists=True), default='.',
              help='Directory to search in')
def find(name: Optional[str], filetype: Optional[str], path: str) -> None:
    """Search for files by name or file type."""
    if not name and not filetype:
        click.echo("Please specify either a name pattern or file type")
        return
        
    if filetype:
        name = f"*.{filetype}"
        
    try:
        matches = []
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, name):
                matches.append(os.path.join(root, filename))
                
        if not matches:
            click.echo("No matching files found")
            return
            
        click.echo("\nFound files:")
        for match in matches:
            rel_path = os.path.relpath(match, path)
            size = os.path.getsize(match)
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/1024/1024:.1f}MB"
            click.echo(f"- {rel_path} ({size_str})")
            
    except PermissionError:
        click.echo("Permission denied: Unable to access some directories")
    except Exception as e:
        click.echo(f"Error searching files: {str(e)}")

@click.command()
@click.argument('prompt')
@click.option('--type', '-t', type=click.Choice(['code', 'text', 'markdown']),
              default='text', help='Type of content to write')
@click.option('--lang', '-l', help='Programming language for code')
@click.option('--path', '-p', type=click.Path(), help='Path to save the file')
@click.option('--generate', '-g', is_flag=True, help='Generate content using AI')
def write(prompt: str, type: str, lang: Optional[str], path: Optional[str],
          generate: bool) -> None:
    """Write or generate content and save to a file."""
    content = prompt
    if generate:
        click.echo(f"\n📝 You asked me to generate: {prompt}")
        try:
            click.echo("\n🤔 CLIche is generating your content...")
            from ..core import CLIche
            cliche = CLIche()
            response = asyncio.run(cliche.ask_llm(f"Generate {type} content: {prompt}"))
            
            # If it's code, extract just the code blocks for the file
            if type == 'code':
                # Extract code blocks for the file
                code_blocks = re.findall(r'```(?:python|bash)?\n(.*?)\n```', response, re.DOTALL)
                if code_blocks:
                    # Find the largest code block (likely the main code)
                    content = max(code_blocks, key=len).strip()
                    
                    # Show explanation (text before the first code block)
                    first_block_start = response.find('```')
                    if first_block_start > 0:
                        explanation = response[:first_block_start].strip()
                        click.echo(f"\n💡 {explanation}")
                    
                    click.echo("\n🚀 Generating code...")
                else:
                    click.echo("\n⚠️ No code blocks found, using full response")
                    content = response
            else:
                content = response
                
        except Exception as e:
            click.echo(f"Error generating content: {str(e)}")
            return
        
    if not path:
        # Save files to ~/.cliche/files/[type]
        cliche_dir = Path.home() / '.cliche' / 'files' / type
        cliche_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a default filename based on content type
        base_name = prompt.lower().replace(' ', '_')[:30]
        if type == 'code' and lang:
            ext = f".{lang}"
        elif type == 'markdown':
            ext = '.md'
        else:
            ext = '.txt'
        path = str(cliche_dir / f"{base_name}{ext}")
        
    try:
        # Create parent directories if they don't exist
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(content)
            
        click.echo(f"\n✨ Content written to: {path}")
        
    except PermissionError:
        click.echo(f"Permission denied: Unable to write to {path}")
    except Exception as e:
        click.echo(f"Error writing file: {str(e)}")
