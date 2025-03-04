"""
Utilities for cleaning markdown documents.
"""
import re

def clean_markdown_document(content):
    """Remove unwanted markdown fences and other formatting issues that could break rendering."""
    # Check if document begins with a markdown fence and remove it
    if content.strip().startswith("```") or content.strip().startswith('```markdown'):
        # Find the first triple backtick
        first_fence_pos = content.find("```")
        # Find the end of that line
        first_newline_after_fence = content.find("\n", first_fence_pos)
        if first_newline_after_fence != -1:
            # Remove everything from the start to the end of the fence line
            content = content[first_newline_after_fence+1:]
    
    # Check if document ends with a markdown fence and remove it
    if content.strip().endswith("```"):
        # Find the last triple backtick
        last_fence_pos = content.rfind("```")
        # Find the start of that line
        last_newline_before_fence = content.rfind("\n", 0, last_fence_pos)
        if last_newline_before_fence != -1:
            # Remove everything from the start of the fence line to the end
            content = content[:last_newline_before_fence]
    
    # Remove ```markdown blocks that might be in the content
    content = re.sub(r'```markdown\s*', '', content)
    content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
    
    # Remove any standalone ``` without a language specifier that might break rendering
    content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE)
    
    # Fix any duplicate heading markers (e.g., ## ## Heading)
    content = re.sub(r'(#+)\s+(#+)', r'\1', content)
    
    # Ensure proper spacing for code blocks (add newlines before and after if missing)
    content = re.sub(r'([^\n])```([a-zA-Z0-9]*)', r'\1\n```\2', content)
    content = re.sub(r'```([a-zA-Z0-9]*)([^\n])', r'```\1\n\2', content)
    
    # Ensure code blocks end properly
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)([^\n])```', r'```\1\n\2\3\n```', content, flags=re.DOTALL)
    
    # Fix code blocks with no language specifier
    content = re.sub(r'```\n', r'```text\n', content)
    
    # Add empty line after code blocks if missing
    content = re.sub(r'```\n([^`\n])', r'```\n\n\1', content)
    
    # Fix broken Python code blocks (```pytho\nn, ```py\nn, ```pyth\nn, etc.)
    content = re.sub(r'```pytho\s*\nn', r'```python\n', content)
    content = re.sub(r'```pyth\s*\nn', r'```python\n', content)
    content = re.sub(r'```py\s*\nn', r'```python\n', content)
    # Generic pattern to fix any language with escaped newlines
    content = re.sub(r'```([a-z]+)\\n', r'```\1\n', content)
    
    # Fix common incomplete language specifiers for Python
    content = re.sub(r'```pytho\s*\n', r'```python\n', content)
    content = re.sub(r'```pyth\s*\n', r'```python\n', content)
    content = re.sub(r'```py\s*\n', r'```python\n', content)
    
    # NEW: Fix specific patterns we see in the document's latter half
    
    # 1. Close code blocks that are followed by bullet points (common in the latter half)
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n\s*-\s+', r'```\1\n\2\n```\n\n- ', content, flags=re.DOTALL)
    
    # 2. Handle bullet points that immediately follow code openings (without proper separation)
    content = re.sub(r'```([a-zA-Z0-9]*)\n\s*-\s+', r'```\1\n\n- ', content, flags=re.MULTILINE)
    
    # 3. Close code blocks before "### Footnotes" and similar section markers
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n#{1,3}\s+([A-Z][a-zA-Z\s]+)', 
                    r'```\1\n\2\n```\n\n### \3', content, flags=re.DOTALL)
    
    # 4. Fix inline code inside code blocks (common in the First Steps section)
    bullet_in_code_pattern = r'```([a-zA-Z0-9]*)\n(.*?)(\n\s*-\s+[^\n]+\n)(.*?)```'
    while re.search(bullet_in_code_pattern, content, re.DOTALL):
        content = re.sub(bullet_in_code_pattern, 
                        r'```\1\n\2\n```\n\3\n```\1\n\4\n```', content, flags=re.DOTALL)
    
    # 5. Close code blocks before table of contents sections
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n(#{1,3}\s+Table of Contents)', 
                    r'```\1\n\2\n```\n\n\3', content, flags=re.DOTALL)
                    
    # 6. Close code blocks before "The output:" text (common pattern in the doc)
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n\s*The output:', 
                    r'```\1\n\2\n```\n\nThe output:', content, flags=re.DOTALL)
    
    # 7. Ensure code blocks are closed before sections starting with "Of course" (seen in example)
    content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n\s*Of course,', 
                    r'```\1\n\2\n```\n\nOf course,', content, flags=re.DOTALL)
    
    # 8. Close code blocks that have a mixture of code and explanatory text (common issue)
    explanatory_text_patterns = [
        r'- The ([a-zA-Z0-9_]+) (line|loop)', 
        r'- In (Python|this)', 
        r'This example', 
        r'Note that',
        r'For more information',
        r'The keyword argument'
    ]
    
    for pattern in explanatory_text_patterns:
        content = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n\s*' + pattern, 
                        r'```\1\n\2\n```\n\n' + pattern, content, flags=re.DOTALL)
    
    # Fix unclosed code blocks
    # Find all opening and closing fences
    code_block_starts = re.findall(r'```[a-zA-Z0-9]*\n', content)
    code_block_ends = re.findall(r'\n```', content)
    
    # If we have more starts than ends, add missing closing fences
    if len(code_block_starts) > len(code_block_ends):
        # Find all positions of starts and ends
        start_positions = [m.start() for m in re.finditer(r'```[a-zA-Z0-9]*\n', content)]
        end_positions = [m.start() for m in re.finditer(r'\n```', content)]
        
        # Track positions that have been processed
        processed_positions = set()
        
        # Check each start position
        for i, start_pos in enumerate(start_positions):
            # Skip if this start has a matching end
            if i < len(end_positions) and start_pos < end_positions[i]:
                processed_positions.add(start_pos)
                continue
                
            # Find next heading or paragraph break after this unclosed block
            next_heading = re.search(r'\n#+\s+', content[start_pos:])
            next_para = re.search(r'\n\s*\n', content[start_pos:])
            next_bullet = re.search(r'\n\s*-\s+', content[start_pos:])
            
            # Determine position to insert closing fence
            insert_pos = start_pos
            insert_positions = []
            if next_heading:
                insert_positions.append(start_pos + next_heading.start())
            if next_para:
                insert_positions.append(start_pos + next_para.start())
            if next_bullet:
                insert_positions.append(start_pos + next_bullet.start())
                
            if insert_positions:
                insert_pos = min(insert_positions)
            else:
                insert_pos = len(content) - 1  # End of content
                
            # Insert closing fence if we haven't processed this position already
            if insert_pos not in processed_positions:
                content = content[:insert_pos] + "\n```\n" + content[insert_pos:]
                processed_positions.add(insert_pos)
    
    # Final safety check - if there are still mismatched code blocks, fix them
    # Count backtick triplets that seem to be code fence markers
    code_fence_markers = re.findall(r'```[a-zA-Z0-9]*\n|```\s*$|\n```', content)
    # If we have an odd number, we need to add one more closing fence at the end
    if len(code_fence_markers) % 2 == 1:
        # Add a closing fence at the end of the document
        content += "\n\n```\n"
        
    # Handle the case where examples and demonstrations turn into code blocks
    example_phrases = [
        r'some examples demonstrate',
        r'examples:',
        r'example:',
        r'for example:',
        r'demonstrates how',
        r'see the following example',
        r'use triple quotes',
        r'string indexing allows',
        r'Lists are',
        r'Lists can be',
        r'Consider this example',
        r'Let\'s look at an example',
        r'Here\'s an example',
        r'As an example',
        r'The following example'
    ]
    
    for phrase in example_phrases:
        # Check if the phrase is followed by a code block that's never closed properly
        pattern = f'({phrase}[^\n]*\n+```[a-zA-Z0-9]*\n)([^`]+)$'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # Add a closing fence immediately after a good break point
            example_text = match.group(2)
            # Find a good break point (paragraph break or heading)
            break_point = max(
                example_text.find('\n\n'), 
                example_text.find('\n#')
            )
            if break_point == -1:
                # If no good break point, just close after a reasonable amount of content
                break_point = min(len(example_text), 500)
            
            # Insert the closing fence
            closing_pos = match.start(2) + break_point
            content = content[:closing_pos] + "\n```\n\n" + content[closing_pos:]
    
    # NEW: Additional final cleaning steps
    
    # 1. Remove any empty code blocks that might have been created during fixes
    content = re.sub(r'```[a-zA-Z0-9]*\n\s*```\n', '', content)
    
    # 2. Fix consecutive code blocks without text in between
    content = re.sub(r'```\n\n```([a-zA-Z0-9]*)', r'```\1', content)
    
    # 3. Ensure a blank line after every code block closing
    content = re.sub(r'```\n([^`\n])', r'```\n\n\1', content)
    
    # 4. Remove trailing whitespace at the end of lines
    content = re.sub(r' +$', '', content, flags=re.MULTILINE)
    
    # 5. Fix spaces around code backticks
    content = re.sub(r'(\S)```', r'\1\n```', content)
    
    # Additional fix for orphaned code blocks by scanning the whole document
    # Find all code block openings
    code_block_starts = list(re.finditer(r'```[a-zA-Z0-9]*\n', content))
    
    # For each start, check if it has a matching closing fence
    for i, start_match in enumerate(code_block_starts):
        start_pos = start_match.end()
        # Find the next code fence (opening or closing)
        next_fence = re.search(r'```', content[start_pos:])
        
        # If no next fence found or it's another opening fence, we need to close this block
        if not next_fence or content[start_pos + next_fence.start() - 3:start_pos + next_fence.start()].strip() == '':
            # Find a good place to close - next heading or paragraph break
            next_heading = re.search(r'\n#+\s+', content[start_pos:])
            next_para = re.search(r'\n\s*\n', content[start_pos:])
            next_bullet = re.search(r'\n\s*-\s+', content[start_pos:])
            
            # Determine position to insert closing fence
            insert_positions = []
            if next_heading: insert_positions.append(start_pos + next_heading.start())
            if next_para: insert_positions.append(start_pos + next_para.start())
            if next_bullet: insert_positions.append(start_pos + next_bullet.start())
            
            if insert_positions:
                insert_pos = min(insert_positions)
            else:
                # If no good break points, insert fence at the end of the document
                insert_pos = len(content)
            
            # Add closing fence
            content = content[:insert_pos] + "\n```\n\n" + content[insert_pos:]
    
    # Final scan - ensure that all ```python are followed by a matching ``` closure
    # This handles code blocks in sections like "### 3.1.5 Lists" that don't get caught by other patterns
    sections = re.split(r'^#{2,}\s+.*$', content, flags=re.MULTILINE)
    result_parts = []
    
    # Process the content in sections
    heading_matches = re.finditer(r'^(#{2,}\s+.*?)$', content, flags=re.MULTILINE)
    headings = [m.group(1) for m in heading_matches]
    
    # Handle the case where the first section doesn't have a heading
    if not content.lstrip().startswith('#'):
        first_heading_pos = content.find('#')
        if first_heading_pos > 0:
            sections = [content[:first_heading_pos]] + sections
            headings = [""] + headings
    
    for i, section in enumerate(sections):
        if i < len(headings):
            current_heading = headings[i]
        else:
            current_heading = ""
            
        # Count code fence markers in this section
        fence_markers = re.findall(r'```', section)
        
        # If odd number of markers, add a closing fence
        if len(fence_markers) % 2 == 1:
            # Find the last code block start
            last_start = section.rfind("```")
            if last_start != -1:
                # Check if this is actually an opening fence
                next_line_start = section[last_start:].find('\n')
                if next_line_start != -1 and last_start + next_line_start + 1 < len(section):
                    # This is likely an opening fence if there's text after ```
                    # Add a closing fence at the end of the section
                    section += "\n```\n"
        
        # Add heading and processed section to result
        if current_heading:
            result_parts.append(current_heading)
        result_parts.append(section)
    
    # Combine processed sections
    content = ''.join(result_parts)
    
    # Remove any legacy [INSERT_IMAGE_X_HERE] placeholders
    content = re.sub(r'\[INSERT_IMAGE_\d+_HERE\]', '', content)
    
    return content 