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
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Ensure you have the following dependencies installed:
- crawl4ai
- beautifulsoup4
- duckduckgo-search
- rich
- pydantic

These are automatically installed when you install CLIche.

## Scrape Command

The `scrape` command extracts content from websites based on a URL and optionally a specific topic. It uses intelligent content extraction to focus on the most relevant information.

### Usage

```bash
cliche scrape URL [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--topic TEXT` | Focus on a specific topic when scraping content |
| `--depth INTEGER` | Maximum crawling depth (default: 1) |
| `--max-pages INTEGER` | Maximum number of pages to scrape (default: 10) |
| `--output TEXT` | Output file name (default: auto-generated) |
| `--format [json\|markdown\|text]` | Output format (default: json) |
| `--debug` | Enable debug mode for verbose output |
| `--help` | Show help message |

### Examples

**Basic scraping of a single page:**
```bash
cliche scrape "https://docs.python.org/3/library/asyncio.html"
```

**Topic-focused scraping with depth:**
```bash
cliche scrape "https://docs.python.org/3/" --topic "Python async" --depth 2
```

**Scraping with custom output file:**
```bash
cliche scrape "https://flask.palletsprojects.com/" --topic "Flask routing" --output flask_routes
```

**Scraping with specific format:**
```bash
cliche scrape "https://react.dev/learn" --topic "React hooks" --format markdown
```

## Generate Command

The `generate` command creates structured documents from previously scraped content, organizing information into a cohesive document with proper sections and formatting.

### Usage

```bash
cliche generate TOPIC [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--format [markdown\|html\|pdf\|text]` | Output format (default: markdown) |
| `--output TEXT` | Output file name (default: auto-generated) |
| `--professional` | Use professional tone (default: use CLIche's snarky tone) |
| `--toc` | Include table of contents (default: true for markdown and HTML) |
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

# Step 3: Generate a document
cliche generate "Python async" --format markdown
```

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

---

Made with ❤️ by Pink Pixel
Dream it, Pixel it ✨ 