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

def get_output_dir(type: Literal['code', 'write']) -> Path:
    """Get the output directory for generated files."""
    # Get user's home directory
    home = Path.home()
    
    # Create base .cliche directory if it doesn't exist
    cliche_dir = home / '.cliche'
    cliche_dir.mkdir(exist_ok=True)
    
    # Create files directory if it doesn't exist
    files_dir = cliche_dir / 'files'
    files_dir.mkdir(exist_ok=True)
    
    # Create type-specific directory if it doesn't exist
    output_dir = files_dir / type
    output_dir.mkdir(exist_ok=True)
    
    return output_dir

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
    """Clean text content for file saving.
    
    - Normalize line endings to \n
    - Remove any zero-width spaces or other invisible characters
    - Ensure proper spacing around headers
    - Remove any BOM if present
    """
    # Remove BOM if present
    content = content.replace('\ufeff', '')
    
    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove zero-width spaces and other invisible characters
    content = re.sub(r'[\u200B-\u200D\uFEFF]', '', content)
    
    # Ensure headers have proper spacing (for markdown)
    content = re.sub(r'(?m)^(#+)([^ \n])', r'\1 \2', content)
    
    # Ensure exactly one newline at the end
    content = content.rstrip('\n') + '\n'
    
    return content

def save_text_to_file(content: str, path: str) -> None:
    """Save text content to a file.
    
    Args:
        content: The text content to save
        path: Path where to save the file
    """
    # Clean the content
    content = clean_text_content(content)
    
    # Write content with UTF-8 encoding and LF line endings
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    
    # Set file mode to 644 (rw-r--r--)
    os.chmod(path, 0o644)

def extract_code_blocks(text: str, lang: Optional[str] = None) -> List[str]:
    """Extract code blocks from text.
    
    Args:
        text: The text to extract code blocks from
        lang: Optional language to filter code blocks
        
    Returns:
        List of code blocks found in the text
    """
    if lang:
        # Look for code blocks with the specified language
        blocks = re.findall(rf'```{lang}\n?(.*?)\n?```', text, re.DOTALL)
        if not blocks:
            # Fallback to any code blocks if none found with specified language
            blocks = re.findall(r'```\n?(.*?)\n?```', text, re.DOTALL)
    else:
        # Get all code blocks
        blocks = re.findall(r'```\n?(.*?)\n?```', text, re.DOTALL)
    return blocks
