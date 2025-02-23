"""
File management commands
"""
import click
import os
import fnmatch
import subprocess
import shutil
from typing import Optional, List, Tuple
import asyncio
import re
from pathlib import Path
import stat

def get_file_size_str(size: int) -> str:
    """Convert file size to human readable string."""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f}KB"
    else:
        return f"{size/1024/1024:.1f}MB"

def search_with_fd(name: str, path: str, hidden: bool, case_sensitive: bool, 
                  max_depth: Optional[int], exclude: List[str]) -> Tuple[bool, List[str], str]:
    """Search files using fd command."""
    cmd = ['fd']
    
    # Basic options
    if not case_sensitive:
        cmd.append('-i')  # Case insensitive
    if hidden:
        cmd.append('-H')  # Include hidden files
    if max_depth is not None:
        cmd.extend(['-d', str(max_depth)])
        
    # Add exclude patterns
    for pattern in exclude:
        cmd.extend(['-E', pattern])
        
    # Add search pattern and path
    cmd.append(name)
    cmd.append(path)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, [], result.stderr
        matches = [m for m in result.stdout.strip().split('\n') if m]
        return True, matches, ""
    except FileNotFoundError:
        return False, [], "fd command not found"
    except subprocess.CalledProcessError as e:
        return False, [], str(e)

def search_with_find(name: str, path: str, hidden: bool, max_depth: Optional[int]) -> List[str]:
    """Search files using find command as fallback."""
    cmd = ['find', path]
    
    if max_depth is not None:
        cmd.extend(['-maxdepth', str(max_depth)])
    
    # Skip special directories
    cmd.extend([
        '(',
        '!', '-path', '*/__pycache__/*',
        '!', '-path', '*/.git/*',
        '!', '-path', '*/.pytest_cache/*',
        '!', '-path', '*/.mypy_cache/*',
        '!', '-path', '*/.coverage/*',
        '!', '-path', '*/.tox/*',
        '!', '-path', '*/.env/*',
        '!', '-path', '*/.venv/*',
        '!', '-path', '*/venv/*',
        '!', '-path', '*/node_modules/*',
        '!', '-path', '*/build/*',
        '!', '-path', '*/dist/*',
        '!', '-path', '*/.idea/*',
        '!', '-path', '*/.vs/*',
        '!', '-path', '*/.vscode/*',
        '!', '-path', '*/vendor/*',
        '!', '-path', '*/go/pkg/*',
        ')',
    ])
    
    if not hidden:
        cmd.extend(['-a', '!', '-path', '*/.*'])  # Exclude hidden files
        
    # Convert glob pattern to find pattern
    if '*' in name or '?' in name:
        cmd.extend(['-a', '-name', name])
    else:
        cmd.extend(['-a', '-name', f'*{name}*'])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return [m for m in result.stdout.strip().split('\n') if m]
    except Exception:
        pass
        
    # If find command fails, fall back to os.walk
    matches = []
    name_pattern = f"*{name}*" if '*' not in name and '?' not in name else name
    special_dirs = {
        '__pycache__', '.git', '.pytest_cache', '.mypy_cache',
        '.coverage', '.tox', '.env', '.venv', 'venv', 'node_modules',
        'build', 'dist', '.idea', '.vs', '.vscode', 'vendor', 'go'
    }
                   
    for root, dirnames, filenames in os.walk(path):
        # Skip special directories
        dirnames[:] = [d for d in dirnames if d not in special_dirs]
        if not hidden:
            # Skip hidden directories
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            
        if max_depth is not None:
            # Skip if we're too deep
            rel_path = os.path.relpath(root, path)
            if rel_path != '.' and len(rel_path.split(os.sep)) > max_depth:
                continue
                
        for filename in fnmatch.filter(filenames, name_pattern):
            if hidden or not filename.startswith('.'):
                matches.append(os.path.join(root, filename))
    return matches

@click.command()
@click.option('--name', '-n', help='File name pattern (e.g., *.txt)')
@click.option('--type', '-t', 'filetype', help='File type (e.g., pdf, jpg)')
@click.option('--path', '-p', type=click.Path(exists=True),
              help='Directory to search in (default: user home)')
@click.option('--hidden/--no-hidden', default=False, help='Include hidden files')
@click.option('--case-sensitive/--no-case-sensitive', default=False, help='Case sensitive search')
@click.option('--max-depth', '-d', type=int, help='Maximum directory depth to search')
@click.option('--exclude', '-e', multiple=True, help='Exclude files/directories matching pattern')
@click.option('--local', '-l', is_flag=True, help='Search only in current directory')
@click.option('--root', '-r', is_flag=True, help='Search from root directory')
def find(name: Optional[str], filetype: Optional[str], path: str | None, hidden: bool,
         case_sensitive: bool, max_depth: Optional[int], exclude: List[str], 
         local: bool, root: bool) -> None:
    """Search for files by name or file type.
    
    By default, searches in user's home directory. Use --local to search in current directory
    or --root to search from root directory.
    
    Examples:
        cliche find -n "*.py"            # Find Python files in home directory
        cliche find -t pdf -l            # Find PDF files in current directory
        cliche find -n "test*" -r        # Find files starting with test from root
        cliche find -t py -d 2           # Find Python files up to 2 directories deep
        cliche find -n "*.log" --hidden  # Find log files including hidden ones
    """
    if not name and not filetype:
        click.echo("Please specify either a name pattern or file type")
        return
        
    if filetype:
        name = f"*.{filetype}"
        
    # Determine search path
    if path:
        search_path = path
    elif local:
        search_path = '.'
    elif root:
        search_path = '/'
    else:
        search_path = os.path.expanduser('~')
        
    try:
        # Try fd first
        success, matches, error = search_with_fd(name, search_path, hidden, case_sensitive, max_depth, exclude)
        if not success:
            if "fd command not found" in error:
                click.echo("Note: For faster searches, install fd-find:")
                click.echo("  Ubuntu/Debian: sudo apt install fd-find")
                click.echo("  macOS: brew install fd")
                click.echo("  Arch Linux: sudo pacman -S fd")
                click.echo("\nFalling back to find command...\n")
            matches = search_with_find(name, search_path, hidden, max_depth)
            
        if not matches:
            click.echo("No matching files found")
            return
            
        click.echo("\nFound files:")
        for match in matches:
            try:
                size = os.path.getsize(match)
                size_str = get_file_size_str(size)
                # Show path relative to search directory
                rel_path = os.path.relpath(match, search_path)
                if os.path.isdir(match):
                    click.echo(f" {rel_path}/")
                else:
                    click.echo(f" {rel_path} ({size_str})")
            except OSError:
                # If we can't get the size, just show the path
                click.echo(f"- {match}")
                
    except Exception as e:
        click.echo(f"Error searching files: {str(e)}")

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
        click.echo(f"\n You asked me to generate: {prompt}")
        try:
            click.echo("\n CLIche is generating your content...")
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
                        click.echo(f"\n {explanation}")
                    
                    click.echo("\n Generating code...")
                else:
                    click.echo("\n No code blocks found, using full response")
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
            
        click.echo(f"\n Content written to: {path}")
        
    except PermissionError:
        click.echo(f"Permission denied: Unable to write to {path}")
    except Exception as e:
        click.echo(f"Error writing file: {str(e)}")
