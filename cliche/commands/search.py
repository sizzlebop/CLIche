"""
Search command for finding files on the computer
"""
import click
import os
import subprocess
import fnmatch
from typing import Optional, List, Tuple
import platform

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

def search_with_find(name: str, path: str, hidden: bool, max_depth: Optional[int]) -> List[str]:
    """Search files using find command as fallback."""
    cmd = ['find', path]
    
    # Add depth limitation if specified
    if max_depth is not None:
        cmd.extend(['-maxdepth', str(max_depth)])
    
    # Skip hidden files/directories if not requested
    if not hidden:
        cmd.append('-not')
        cmd.append('-path')
        cmd.append('*/.*')
    
    # Add name pattern
    cmd.extend(['-name', name])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return []
        matches = [m for m in result.stdout.strip().split('\n') if m]
        return matches
    except Exception:
        return []

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
def search(name: Optional[str], filetype: Optional[str], path: str | None, hidden: bool,
         case_sensitive: bool, max_depth: Optional[int], exclude: List[str], 
         local: bool, root: bool) -> None:
    """Search for files by name or file type.
    
    By default, searches in user's home directory. Use --local to search in current directory
    or --root to search from root directory.
    
    Examples:
        cliche search -n "*.py"            # Find Python files in home directory
        cliche search -t pdf -l            # Find PDF files in current directory
        cliche search -n "test*" -r        # Find files starting with test from root
        cliche search -t py -d 2           # Find Python files up to 2 directories deep
        cliche search -n "*.log" --hidden  # Find log files including hidden ones
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
                if platform.system() == "Linux":
                    click.echo("  Ubuntu/Debian: sudo apt install fd-find")
                    click.echo("  Arch Linux: sudo pacman -S fd")
                elif platform.system() == "Darwin":
                    click.echo("  macOS: brew install fd")
                elif platform.system() == "Windows":
                    click.echo("  Windows (scoop): scoop install fd")
                    click.echo("  Windows (choco): choco install fd")
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
                    click.echo(f"📁 {rel_path}/")
                else:
                    click.echo(f"📄 {rel_path} ({size_str})")
            except OSError:
                # If we can't get the size, just show the path
                click.echo(f"- {match}")
                
    except Exception as e:
        click.echo(f"Error searching files: {str(e)}") 