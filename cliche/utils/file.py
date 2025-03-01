"""
File management utilities for CLIche.
"""
import os
import re
from pathlib import Path
from typing import List, Optional, Literal

def get_file_size_str(size: int) -> str:
    """Convert file size to human readable string."""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f}KB"
    else:
        return f"{size/1024/1024:.1f}MB"

def get_output_dir(type: Literal['code', 'write', 'scrape', 'docs']) -> Path:
    """Get the output directory for generated files.
    
    Args:
        type: The type of content, which determines the directory.
            - 'code': Code files
            - 'write': Text files from the write command
            - 'scrape': Raw scraped content
            - 'docs': Generated documents, with optional subdirectory
            
    Returns:
        Path object for the output directory
    """
    # Get user's home directory
    home = Path.home()
    
    # Create base cliche directory if it doesn't exist (removing the dot to make it visible)
    cliche_dir = home / 'cliche'
    cliche_dir.mkdir(exist_ok=True)
    
    # Create files directory if it doesn't exist
    files_dir = cliche_dir / 'files'
    files_dir.mkdir(exist_ok=True)
    
    # Create type-specific directory if it doesn't exist
    output_dir = files_dir / type
    output_dir.mkdir(exist_ok=True)
    
    return output_dir

def get_docs_dir(source: Optional[Literal['write', 'research', 'scrape']] = None) -> Path:
    """Get the output directory for documents with optional source-specific subdirectory.
    
    Args:
        source: Optional source type for subdirectory organization
            - 'write': Documents from the write command
            - 'research': Documents from research command
            - 'scrape': Documents generated from scraped content
            
    Returns:
        Path object for the documents directory
    """
    # First get the base docs directory
    docs_dir = get_output_dir('docs')
    
    # If source is specified, create and return source-specific subdirectory
    if source:
        source_dir = docs_dir / source
        source_dir.mkdir(exist_ok=True)
        return source_dir
    
    return docs_dir

def get_image_dir() -> Path:
    """Get the directory for images.
    
    Returns:
        Path object for the images directory
    """
    # Get user's home directory
    home = Path.home()
    
    # Create base cliche directory
    cliche_dir = home / 'cliche'
    cliche_dir.mkdir(exist_ok=True)
    
    # Create files directory
    files_dir = cliche_dir / 'files'
    files_dir.mkdir(exist_ok=True)
    
    # Create images directory
    images_dir = files_dir / 'images'
    images_dir.mkdir(exist_ok=True)
    
    return images_dir

def get_scraped_images_dir() -> Path:
    """Get the directory for scraped images.
    
    Returns:
        Path object for the scraped images directory
    """
    images_dir = get_image_dir()
    
    # Create scraped images directory
    scraped_dir = images_dir / 'scraped'
    scraped_dir.mkdir(exist_ok=True)
    
    return scraped_dir

def save_code_to_file(content: str, path: str) -> None:
    """Save code content to a file."""
    # Ensure the content ends with a newline
    if not content.endswith('\n'):
        content += '\n'
    
    # Write the content
    with open(path, 'w') as f:
        f.write(content)
    
    # Make the file executable if it's a script
    if path.endswith('.py') or path.endswith('.sh'):
        os.chmod(path, 0o755)

def clean_text_content(content: str) -> str:
    """Clean text content for saving."""
    # Remove multiple newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Remove trailing whitespace
    content = '\n'.join(line.rstrip() for line in content.splitlines())
    
    # Ensure single newline at end
    content = content.strip() + '\n'
    
    return content

def clean_content(content: str) -> str:
    """Clean content for saving to file."""
    # Remove invisible characters
    content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
    
    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove multiple newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Remove trailing whitespace
    content = '\n'.join(line.rstrip() for line in content.splitlines())
    
    # Ensure single newline at end
    content = content.strip() + '\n'
    
    return content

def save_content_to_file(content: str, file_type: str, file_name: str, category: str = 'write') -> str:
    """Save content to a file with proper extension and return the path."""
    # Clean the content
    content = clean_content(content)
    
    # Get the output directory
    output_dir = get_output_dir(category)
    
    # Add extension if not present
    if not file_name.endswith(f'.{file_type}'):
        file_name = f"{file_name}.{file_type}"
    
    # Create full path
    file_path = output_dir / file_name
    
    # Save the content
    with open(file_path, 'w') as f:
        f.write(content)
    
    return str(file_path)

def save_text_to_file(content: str, path: str) -> None:
    """Save text content to a file."""
    # Clean the content
    content = clean_text_content(content)
    
    # Write the content
    with open(path, 'w') as f:
        f.write(content)

def extract_code_blocks(text: str, lang: Optional[str] = None) -> List[str]:
    """
    Extract code blocks from text.
    
    Args:
        text: The text to extract code blocks from
        lang: Optional language to filter code blocks
        
    Returns:
        List of code blocks found in the text
    """
    # Pattern to match code blocks with or without language
    pattern = r'```(?:' + (lang or '[^\n]*') + r')?\n(.*?)\n```'
    
    # Find all code blocks
    blocks = re.findall(pattern, text, re.DOTALL)
    
    # Clean and return the blocks
    return [block.strip() for block in blocks]

def get_unique_filename(directory: Path, base_filename: str) -> str:
    """Ensure a filename is unique by adding an incrementing number if needed.
    
    Args:
        directory: Directory where the file will be saved
        base_filename: The initial filename without uniqueness checks
        
    Returns:
        A unique filename that doesn't exist in the directory
    """
    # If file doesn't exist, return the base filename
    file_path = directory / base_filename
    if not file_path.exists():
        return base_filename
    
    # If file exists, try adding numerical suffixes until we find an unused name
    # First, separate filename and extension
    if '.' in base_filename:
        name, ext = base_filename.rsplit('.', 1)
        ext = '.' + ext
    else:
        name, ext = base_filename, ''
    
    # Try adding incremental numbers
    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        file_path = directory / new_filename
        if not file_path.exists():
            return new_filename
        counter += 1
