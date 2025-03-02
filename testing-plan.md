
## Testing Plan for Scrape Functionality

Let's thoroughly test the scraping functionality with different sites and options to ensure everything is working correctly. I'll provide a series of commands to test various aspects of the system:

### 1. Basic Wikipedia Scraping (Specialized Extractor)

#### This should use the WikipediaExtractor
```
cliche scrape "https://en.wikipedia.org/wiki/Python_(programming_language)" --verbose
```
Expected output:
Should identify it's using the Wikipedia extractor
Should extract structured content with headings
Should save a JSON file to ~/cliche/files/scrape/

### 2. Scraping with Images
# Test image extraction
```
cliche scrape "https://en.wikipedia.org/wiki/Artificial_intelligence" --images --verbose
```
Expected output:
Should extract images and save them to ~/cliche/files/images/scraped/
Should report how many images were extracted
Images should be referenced in the JSON file

### 3. Multi-page Crawling
```
cliche scrape "https://en.wikipedia.org/wiki/Artificial_intelligence" --verbose
```
Expected output:
Should crawl multiple pages within the Python docs
Should extract content from multiple pages
Should follow links within the same domain

### 4. Topic-focused Scraping
```
cliche scrape "https://en.wikipedia.org/wiki/Artificial_intelligence" --verbose
```
Expected output:
Should extract content relevant to "neural networks"
Should prioritize sections about neural networks
Should mention relevance scoring

### 5. Python.org Specialized Extraction
```
cliche scrape "https://en.wikipedia.org/wiki/Artificial_intelligence" --verbose
```
Expected output:
Should identify it's using the Python docs extractor
Should extract code blocks with proper formatting
Should handle Python-specific content well

### 6. Document Generation
```
cliche scrape "https://en.wikipedia.org/wiki/Artificial_intelligence" --verbose
```
Expected output:
Should generate a comprehensive document from the scraped content
Should include images in the document
Should structure the content with proper headings

### 7. Scrape Without LLM Enhancement
```
cliche scrape "https://en.wikipedia.org/wiki/Artificial_intelligence" --verbose
```
Expected output:
Should mention "LLM extraction disabled"
Should still extract structured content using BeautifulSoup
Extraction should be faster but potentially less refined

### 8. Testing Individual Components

To test for import issues in different commands:
Each command should display help information without any import errors.
Examining Results
After running these tests, let's examine the files:
Check the JSON files in ~/cliche/files/scrape/
Look at the images in ~/cliche/files/images/scraped/
Review generated documents in ~/cliche/files/docs/scrape/
This comprehensive testing should help identify any issues with the integration, imports, or functionality of the scraping system.