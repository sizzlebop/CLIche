#!/usr/bin/env python3
"""
Simple integration test for the new ImageExtractor.
"""
import os
import sys
import asyncio
import requests
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cliche.scraping.extractors.image_extractor import ImageExtractor

async def test_extraction(url, output_dir=None):
    """Test the new ImageExtractor on a real website."""
    print(f"Fetching {url}...")
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    response.raise_for_status()
    html_content = response.text
    
    print(f"Extracting images...")
    extractor = ImageExtractor()
    images = await extractor.extract_images(
        html_content=html_content,
        base_url=url,
        max_images=10,
        min_size=200,  # Increased minimum size
        output_dir=output_dir
    )
    
    print(f"Found {len(images)} images:")
    for idx, image in enumerate(images, 1):
        print(f"\nImage {idx}:")
        print(f"  URL: {image.url}")
        print(f"  Alt text: {image.alt_text}")
        print(f"  Caption: {image.caption}")
        print(f"  Dimensions: {image.width}x{image.height}")
        if image.local_path:
            print(f"  Local path: {image.local_path}")
            print(f"  File exists: {os.path.exists(image.local_path)}")
    
    return images

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Default to a Wikipedia article, which usually has images
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    
    output_dir = Path("./test_images") if len(sys.argv) <= 2 else Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Running image extraction test...")
    asyncio.run(test_extraction(url, output_dir))
    print("\nTest completed successfully!") 