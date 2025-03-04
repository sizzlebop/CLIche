# CLIche Web Scraping

CLIche includes powerful web scraping capabilities that allow you to extract and save content from websites directly from your terminal. The `scrape` command enables focused content extraction, while the `generate` command helps you create structured documents from the scraped content.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Scrape Command](#scrape-command)
  - [Usage](#usage)
  - [Options](#options)
  - [Examples](#examples)
- [Generate Command](#generate-command)
  - [Usage](#usage-1)
  - [Options](#options-1)
  - [Examples](#examples-1)
- [Helper Scripts](#helper-scripts)
- [Document Generation Modes](#document-generation-modes)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## What's New

### Enhanced Extraction (v1.4.0)

- **Browser-Based Rendering**: Improved JavaScript content support using direct browser automation
- **Higher Character Limits**: Extract up to 1 million characters per site (previously 50,000)
- **Detailed Progress**: Step-by-step console output showing fetch and extraction progress
- **Specialized Extractors**: Optimized extraction for Wikipedia and Python documentation
- **Performance Improvements**: Faster and more reliable content processing

## Prerequisites

Ensure you have the following dependencies installed:
- crawl4ai
- beautifulsoup4
- duckduckgo-search
- rich
- pydantic

These are automatically installed when you install CLIche.

## Scrape Command

The `scrape` command extracts structured content from websites.

### Usage

```bash
cliche scrape [OPTIONS] URL
```

### Options

| Option | Description |
|--------|-------------|
| `--topic, -t TEXT` | Topic of the scrape |
| `--depth, -d INTEGER` | Depth of the scrape (levels of links to follow) (default: 3) |
| `--max-pages, -m INTEGER` | Maximum number of pages to crawl (default: 3) |
| `--debug` | Enable debug mode with detailed error messages |
| `--fallback-only` | Skip primary crawler and use only the fallback scraper |
| `--write, -w` | Generate a document instead of terminal output |
| `--format, -f [text\|markdown\|html]` | Document format when using --write (default: markdown) |
| `--filename` | Optional filename for the generated document |
| `--image, -i TEXT` | Add images related to the topic by search term |
| `--image-count INTEGER` | Number of images to add (default: 3) |
| `--image-width INTEGER` | Width of images (default: 800) |
| `--search-engine [auto\|duckduckgo\|brave]` | Search engine to use (auto tries all available) |
| `--summarize` | Generate a concise summary document instead of a comprehensive one |
| `--snippet` | Generate a very brief snippet/overview (few paragraphs) |

### Examples

**Basic Usage:**
```bash
# Scrape a single URL without following links
cliche scrape https://docs.github.com
```

**Advanced Usage with Link Following:**
```bash
# Follow links 2 levels deep, maximum 5 pages total
cliche scrape https://docs.python.org/3/library/asyncio.html --depth 2 --max-pages 5

# Enable debug mode to see detailed information about the scraping process
cliche scrape https://docs.python.org --depth 3 --max-pages 10 --debug
```

**Generate Documents:**
```bash
# Scrape and generate a markdown document
cliche scrape https://flask.palletsprojects.com --depth 1 --write --format markdown

# Scrape and generate a document with images
cliche scrape https://docs.python.org/3/tutorial/ --depth 2 --write --image "python programming" --image-count 2
```

## Generate Command

The `generate` command creates well-structured documents from previously scraped content. It uses an LLM to organize and format the data into a coherent document, optionally enhancing it with images.

### Usage

```bash
cliche generate TOPIC [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--format [text\|markdown\|html]` | Output format (default: markdown) |
| `--path TEXT` | Optional path to save the file |
| `--raw` | Generate raw merged content without LLM processing |
| `--professional` | Use professional tone (default: snarky) |
| `--summarize` | Generate a concise summary instead of comprehensive content |
| `--image TEXT` | Add images related to the topic by search term |
| `--image-count INTEGER` | Number of images to add (default: 3) |
| `--image-width INTEGER` | Width of images in pixels (default: 800) |
| `--debug` | Enable debug mode for verbose output |
| `--help` | Show help message |

### Examples

**Generate a markdown document from previously scraped content:**
```bash
cliche generate "Python async"
```

**Generate an HTML document with professional tone:**
```bash
cliche generate "Flask routing" --format html --professional
```

**Generate a PDF document with custom filename:**
```bash
cliche generate "React hooks" --format pdf --output react_hooks_guide
```

**Generate a document with images using direct URLs:**
```bash
cliche generate "React hooks" --format markdown --image "react programming" --image-count 2
```

**Generate an HTML document with professional tone and images:**
```bash
cliche generate "Flask routing" --format html --professional --image "flask framework" --image-width 1024
```

## Helper Scripts

CLIche provides helper scripts to simplify common scraping and document generation workflows:

### scrape.sh

```bash
./scrape.sh URL TOPIC DEPTH MAX_PAGES
```

Example:
```bash
./scrape.sh "https://docs.python.org/3/" "Python async" 2 10
```

### generate.sh

```bash
./generate.sh TOPIC FORMAT
```

Example:
```bash
./generate.sh "Python async" markdown
```

## Document Generation Modes

The `generate` command supports two main modes of operation: comprehensive and summary modes, controlled by the `--summarize` flag.

### Comprehensive Mode (Default)

When running the command without the `--summarize` flag, CLIche uses an advanced chunking approach to generate detailed, complete documentation:

```bash
cliche generate "Python async" --format markdown
```

The comprehensive mode:

1. **Preserves All Technical Details**: Unlike the summary mode, comprehensive mode retains all technical details, code examples, and in-depth explanations from the source material.

2. **Uses Intelligent Chunking**: The system:
   - Extracts major sections from scraped content
   - Identifies natural section boundaries (headings, capitalized titles, etc.)
   - Creates artificial sections when natural boundaries aren't found
   - Processes each section individually with the LLM to ensure high quality
   - Combines sections into a cohesive document with proper structure

3. **Handles Large Content Volumes**: By breaking content into chunks of 2000-3000 characters each, it can process much larger documents than would fit in a single LLM context window.

4. **Maintains Document Structure**: The chunking approach preserves proper document structure with:
   - Consistent title and introduction
   - Automatically generated table of contents
   - Well-organized sections based on content
   - Proper conclusion that summarizes main points

### Summary Mode

When you need a more concise output, use the `--summarize` flag:

```bash
cliche generate "Python async" --format markdown --summarize
```

The summary mode:
- Generates a shorter, more focused document
- Extracts and condenses the most important information
- Follows a more traditional approach without advanced chunking
- Is ideal for quick reference documents

### When to Use Each Mode

- **Use Comprehensive Mode (Default) When:**
  - You need all technical details and examples
  - The full depth of information is important
  - You're creating reference documentation

- **Use Summary Mode When:**
  - You need a quick overview
  - File size and brevity are priorities
  - You want a condensed version for quick scanning

## Advanced Usage

### Multi-Stage Research and Documentation

For comprehensive documentation on a topic:

```bash
# Step 1: Scrape multiple related sources
cliche scrape "https://docs.python.org/3/library/asyncio.html" --topic "Python async" --depth 1
cliche scrape "https://realpython.com/async-io-python/" --topic "Python async" --depth 1

# Step 2: Generate a comprehensive document
cliche generate "Python async" --format markdown --professional
```

### Combining with Research Command

The `research` command can help identify the best sources before scraping:

```bash
# Step 1: Research to find relevant sources
cliche research "Python async programming" --depth 3

# Step 2: Scrape the most relevant source
cliche scrape "https://realpython.com/async-io-python/" --topic "Python async" --depth 2

# Step 3: Generate a document with images
cliche generate "Python async" --format markdown --image "python coding" --image-count 2
```

### Image Integration with Direct URLs

When using the `--image` option with the `generate` command, CLIche embeds images with direct URLs from Unsplash instead of downloading them locally. This offers several advantages:

1. **Better compatibility** - Works with all markdown viewers and platforms
2. **Improved sharing** - Documents can be shared without needing to include image files
3. **Standard compliance** - Uses standard markdown image syntax

### AI-Powered Contextual Image Placement

The `generate` command features intelligent image placement powered by AI:

- **Content Analysis**: The AI analyzes your document content to understand the topics, concepts, and structure
- **Contextual Placement**: Images are automatically placed at positions where they best enhance understanding
- **Smart Fallbacks**: If optimal positions can't be determined, images are evenly distributed at logical points
- **Consistent Experience**: Uses the same approach across all document generation commands

This feature works automatically when adding images to generated documents without requiring manual image placeholders. The system will:

1. Analyze the document content to identify key concepts and section transitions
2. Determine optimal placement points based on content relevance
3. Insert images at these contextually appropriate positions
4. Add proper attribution for all images as required by Unsplash

Example of using AI-powered image placement with generate command:

```bash
cliche generate "Machine Learning" --format markdown --image "neural networks" --image-count 3
```

This will create a document about machine learning with three neural network images intelligently placed at contextually relevant positions throughout the document.

## Troubleshooting

### Content Extraction Issues

If the scraper fails to extract content properly:

1. **Try increasing depth**: Some websites structure content across multiple pages
   ```bash
   cliche scrape "https://example.com" --depth 2
   ```

2. **Specify a more focused topic**: This helps the scraper identify relevant content
   ```bash
   cliche scrape "https://example.com" --topic "Specific Feature X"
   ```

3. **Enable debug mode**: See detailed information about the extraction process
   ```bash
   cliche scrape "https://example.com" --debug
   ```

### Website Blocking

Some websites block scraping attempts. In these cases:

1. Try using the `research` command instead, which uses different extraction methods:
   ```bash
   cliche research "My Topic" --depth 3
   ```

2. If a website returns a 403 Forbidden error, it likely has anti-scraping measures in place. Try finding alternative sources.

## Advanced Features

### Multi-Page Content Extraction

The scrape command supports sophisticated multi-page content extraction using two key parameters:

- **depth**: Controls how many levels of links to follow
  - `depth=1`: Scrapes only the specified URL (default)
  - `depth=2`: Scrapes the URL and follows links from that page
  - `depth=3+`: Follows links multiple levels deep

- **max-pages**: Limits the total number of pages scraped
  - Controls the maximum number of pages processed across all depth levels
  - Prevents excessive scraping of large websites
  - Default is 3 pages total

The system intelligently scales content limits based on depth:
- Each depth level increases the character limit by 100,000 chars
- With `depth=3`, the total character limit would be 300,000 chars

**How Link Following Works:**

1. The crawler starts with the provided URL
2. When `depth > 1`, it identifies and follows links within the same domain
3. For each followed link, it extracts content using the same process
4. Content from all pages is combined with separators between pages
5. The total content is limited based on the depth parameter (100,000 × depth)

**Best Practices:**

- For simple documentation sites, `--depth 1` may be sufficient
- For complex, interconnected documentation, try `--depth 2 --max-pages 5`
- For comprehensive research, use `--depth 3 --max-pages 10`
- Always use `--debug` when experimenting to see the crawler configuration

### Using Debug Mode

The `--debug` flag provides valuable information about the scraping process:

```bash
cliche scrape https://docs.github.com --depth 2 --max-pages 5 --debug
```

Debug output includes:
- Crawler configuration details (link following, page limits)
- Content limit information based on depth
- Available crawler methods
- Processing progress for multi-page extraction
- Content extraction metrics (size, page count)
- Detailed error information when failures occur

This is particularly helpful when troubleshooting or when you need to understand how the crawler is processing a specific website.

---

Made with ❤️ by Pink Pixel
Dream it, Pixel it ✨ 