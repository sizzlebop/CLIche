# Migration Guide: Image Scraping

## Overview

CLIche has introduced a new image scraping architecture. The original `image_scraper.py` module is now maintained as a compatibility layer and will be deprecated in future versions.

## Benefits of the New Architecture

- Better error handling
- Improved logging
- Consistent API across extractors
- Better support for different image types
- Improved performance

## Migration from Old to New API

### Before:
```python
from cliche.utils.image_scraper import extract_and_download_images

images = extract_and_download_images(
    html_content=html,
    base_url="https://example.com",
    max_images=10,
    min_size=100,
    output_dir=Path("./images")
)
```

### After:
```python
from cliche.scraping.extractors.image_extractor import ImageExtractor

extractor = ImageExtractor()
images = await extractor.extract_images(
    html_content=html,
    base_url="https://example.com",
    max_images=10,
    min_size=100,
    output_dir=Path("./images")
)
```

### Synchronous Usage

If you need synchronous behavior:

```python
import asyncio
from cliche.scraping.extractors.image_extractor import ImageExtractor

extractor = ImageExtractor()
images = asyncio.run(extractor.extract_images(
    html_content=html,
    base_url="https://example.com",
    max_images=10,
    min_size=100,
    output_dir=Path("./images")
))
```

## Timeline

- v1.0.0: Compatibility layer provided
- v1.1.0: Deprecation warnings added
- v2.0.0: Old API will be removed 