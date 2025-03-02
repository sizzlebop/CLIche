"""Utilities for enhancing scraped content with LLM capabilities."""
import logging
import os
from typing import Dict, Any, Optional, List, Union
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def json_serializable(data: Any) -> Any:
    """Convert data to be JSON serializable."""
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {k: json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [json_serializable(i) for i in data]
    return data

async def enhance_content_with_llm(
    content: Dict[str, Any], 
    topic: Optional[str] = None, 
    provider: Any = None
) -> Dict[str, Any]:
    """
    Enhance scraped content using an LLM provider.
    
    Args:
        content: The scraped content dictionary
        topic: Optional topic to focus on
        provider: The LLM provider to use
        
    Returns:
        Enhanced content dictionary
    """
    if not provider:
        logger.warning("No LLM provider available, skipping enhancement")
        return content
        
    if os.environ.get("CLICHE_NO_LLM"):
        logger.info("LLM enhancement disabled via environment variable")
        return content
        
    try:
        # Make content serializable for prompt
        serializable_content = json_serializable(content)
        
        # Create a prompt for the LLM
        prompt = f"""
        I need you to enhance and improve this scraped web content.
        
        Topic: {topic or 'General information'}
        
        Content: {serializable_content}
        
        Please provide an improved version with:
        1. Better organization and structure
        2. Clearer headings and sections
        3. Improved formatting with proper markdown
        4. Removal of redundant or unnecessary content
        5. Enhanced clarity and readability
        
        Return ONLY the improved content as a valid JSON object with the same structure as the input.
        """
        
        # Generate enhanced content
        response = await provider.generate_response(prompt, professional_mode=True)
        
        # Try to parse the response as JSON
        try:
            # Try to extract JSON from the response
            json_pattern = r'```json\n(.*?)\n```'
            json_match = re.search(json_pattern, response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no code block, try to find JSON directly
                json_str = response.strip()
                
            # Parse the JSON
            enhanced_content = json.loads(json_str)
            return enhanced_content
        except Exception as json_err:
            # If JSON parsing fails, return original content
            return content
            
    except Exception as e:
        logger.error(f"Error enhancing content with LLM: {str(e)}")
        # Return original content on error
        return content
        
async def generate_summary(content: Dict[str, Any], provider=None) -> Optional[str]:
    """
    Generate a summary of the content.
    
    Args:
        content: The scraped content dictionary
        provider: The LLM provider to use
        
    Returns:
        A summary string or None if generation fails
    """
    if not provider:
        return None
        
    try:
        title = content.get('title', '')
        description = content.get('description', '')
        main_content = content.get('main_content', '')
        
        # Truncate if necessary
        if len(main_content) > 8000:
            text_to_summarize = main_content[:8000] + "..."
        else:
            text_to_summarize = main_content
            
        prompt = f"""Generate a concise summary (3-5 paragraphs) of the following content:
        
Title: {title}
Description: {description}

{text_to_summarize}

Summary:"""

        summary = await provider.generate(prompt, temperature=0.3)
        return summary.strip() if summary else None
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return None 