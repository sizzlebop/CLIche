"""Utilities for scraping."""
from .html_processing import (
    extract_table_as_markdown,
    detect_code_language,
    process_code_block,
    process_div_content,
    is_relevant_content,
    clean_html
)

__all__ = [
    'extract_table_as_markdown',
    'detect_code_language',
    'process_code_block',
    'process_div_content',
    'is_relevant_content',
    'clean_html'
] 