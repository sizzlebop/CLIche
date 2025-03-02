"""Utilities for HTML processing and content extraction."""
import re
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)

def extract_table_as_markdown(table: Tag) -> str:
    """Convert an HTML table to markdown format."""
    markdown_table = []
    
    # Extract headers
    headers = []
    for th in table.find_all('th'):
        headers.append(th.get_text(strip=True))
    
    # Use first row if no headers
    if not headers and table.find('tr'):
        headers = [td.get_text(strip=True) for td in table.find('tr').find_all(['td', 'th'])]
    
    if not headers:
        return ""
        
    # Add header row
    markdown_table.append("| " + " | ".join(headers) + " |")
    markdown_table.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    # Add data rows
    start_idx = 0 if not table.find('th') else 1
    for row in table.find_all('tr')[start_idx:]:
        cells = []
        for cell in row.find_all(['td', 'th']):
            text = cell.get_text(strip=True).replace('|', '\\|')
            cells.append(text)
        if cells:
            markdown_table.append("| " + " | ".join(cells) + " |")
    
    return "\n".join(markdown_table)

def detect_code_language(element: Tag, code_text: str) -> str:
    """Detect programming language from code element or content."""
    # Check for language in class attributes
    if element.get('class'):
        for cls in element.get('class'):
            if isinstance(cls, str):
                if cls.startswith('language-'):
                    return cls.replace('language-', '')
                if cls in ['python', 'javascript', 'java', 'ruby', 'php', 'cpp', 'csharp', 'go', 'rust']:
                    return cls
    
    # Try parent elements
    parent = element.parent
    if parent and parent.get('class'):
        for cls in parent.get('class'):
            if isinstance(cls, str):
                if cls.startswith('language-'):
                    return cls.replace('language-', '')
                if 'highlight-' in cls:
                    return cls.replace('highlight-', '')
    
    # Try to infer from content
    if 'def ' in code_text and ':' in code_text:
        return 'python'
    if 'function ' in code_text and '{' in code_text:
        return 'javascript'
    if 'public class ' in code_text:
        return 'java'
    if 'import React' in code_text:
        return 'jsx'
    if '<template>' in code_text and '<script>' in code_text:
        return 'vue'
    if '@Component' in code_text:
        return 'typescript'
    
    # Default to text if no language detected
    return 'text'

def process_code_block(element: Tag, content_text: List[str]):
    """Process a code block element and append to content_text."""
    code_text = element.get_text(strip=True)
    if not code_text:
        return
        
    lang = detect_code_language(element, code_text)
    content_text.append(f"```{lang}\n{code_text}\n```\n\n")

def process_div_content(div: Tag) -> str:
    """Recursively process content in div elements."""
    result = []
    for child in div.children:
        if not hasattr(child, 'name'):
            continue
            
        if child.name == 'p':
            text = child.get_text(strip=True)
            if text:
                result.append(f"{text}\n\n")
        elif child.name in ['ul', 'ol']:
            for li in child.find_all('li', recursive=True):
                li_text = li.get_text(strip=True)
                if li_text:
                    result.append(f"* {li_text}\n")
            result.append("\n")
        elif child.name in ['pre', 'code']:
            code_text = child.get_text(strip=True)
            if code_text:
                lang = detect_code_language(child, code_text)
                result.append(f"```{lang}\n{code_text}\n```\n\n")
        elif child.name == 'div':
            nested_content = process_div_content(child)
            if nested_content:
                result.append(nested_content)
                
    return "\n".join(result)

def is_relevant_content(content: str, topic: Optional[str]) -> bool:
    """Check if content is relevant to a given topic."""
    if not topic or not content:
        return True  # No filtering if no topic specified
        
    # Normalize
    content_lower = content.lower()
    topic_words = topic.lower().split()
    
    # Return true if all topic words are in content
    return all(word in content_lower for word in topic_words)

def clean_html(soup: BeautifulSoup) -> None:
    """Remove unwanted elements from HTML."""
    # Elements that are typically not useful for content extraction
    selectors = [
        'script', 'style', 'iframe', 'nav', 'footer', 'header',
        '.navigation', '.menu', '.sidebar', '.footer', '.header', '.nav',
        '.comments', '.advertisement', '.ad', '.share', '#comments',
        'form', 'aside'
    ]
    
    # Remove each unwanted element
    for selector in selectors:
        for element in soup.select(selector):
            element.decompose()
            
    # Remove empty elements
    for element in soup.find_all(recursive=True):
        if not element.get_text(strip=True) and not element.find_all('img'):
            element.decompose()

def is_element_node(element) -> bool:
    """
    Check if a BeautifulSoup object is an element node (not a string or comment).
    
    Args:
        element: A BeautifulSoup object
        
    Returns:
        bool: True if it's an element node, False otherwise
    """
    return (
        element is not None and 
        hasattr(element, 'name') and 
        element.name is not None and
        element.name != 'None'
    )

def has_attribute(element, attr_name: str) -> bool:
    """
    Safely check if an element has a specific attribute.
    
    Args:
        element: A BeautifulSoup element
        attr_name: The attribute name to check
        
    Returns:
        bool: True if it has the attribute, False otherwise
    """
    return is_element_node(element) and hasattr(element, 'get') and element.get(attr_name) is not None 