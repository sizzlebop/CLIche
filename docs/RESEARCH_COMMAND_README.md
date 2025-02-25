# CLIche Research Command

The `research` command allows you to obtain up-to-date information from the web directly from your terminal. It leverages the power of search engines, smart web crawling, and LLM processing to provide comprehensive answers to your queries based on current information.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Options](#options)
- [Examples](#examples)
- [How It Works](#how-it-works)
- [Professional Mode](#professional-mode)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Prerequisites

Ensure you have the following dependencies installed:
- crawl4ai
- duckduckgo-search
- beautifulsoup4
- rich
- pydantic

These are automatically installed when you install CLIche.

## Usage

```bash
cliche research "Your query here" [OPTIONS]
```

## Options

| Option | Description |
|--------|-------------|
| `--depth INTEGER` | Number of sources to search (default: 3) |
| `--write` | Save the results to a document |
| `--format [markdown\|html\|text]` | Output format when using --write (default: markdown) |
| `--output TEXT` | Custom output file name when using --write |
| `--professional` | Use professional tone (default: CLIche's snarky tone) |
| `--debug` | Enable debug mode for verbose output |
| `--help` | Show help message |

## Examples

**Basic research query:**
```bash
cliche research "Current trends in quantum computing"
```

**Research with increased depth (more sources):**
```bash
cliche research "History of artificial intelligence" --depth 5
```

**Generate a markdown document with the research results:**
```bash
cliche research "Climate change mitigation strategies" --write --format markdown
```

**Save results to a custom file with professional tone:**
```bash
cliche research "Best practices for Docker containers" --write --output docker_guide --professional
```

**Debug mode for troubleshooting:**
```bash
cliche research "Tell me a joke" --debug
```

## How It Works

The research command follows these steps:

1. **Search Phase**: 
   - Uses DuckDuckGo to find relevant sources for your query
   - Ranks results by relevance and recency

2. **Content Extraction Phase**:
   - Crawls each source to extract valuable content
   - Uses adaptive extraction techniques for different site structures
   - Falls back to BeautifulSoup extraction if primary extraction fails

3. **Processing Phase**:
   - Aggregates content from multiple sources
   - Removes duplicative information
   - Organizes content by relevance and logical flow

4. **Response Generation**:
   - Processes aggregated content using the configured LLM
   - Applies selected tone (snarky or professional)
   - Formats output for terminal display or document generation

## Professional Mode

By default, CLIche maintains its snarky personality when presenting research results. For more formal or educational contexts, use the `--professional` flag to generate responses with a professional tone.

**Example with snarky tone (default):**
```bash
cliche research "Benefits of exercise"
```

**Same query with professional tone:**
```bash
cliche research "Benefits of exercise" --professional
```

## Troubleshooting

### Common Issues

1. **Website Access Denied (403 Errors)**:
   - Some websites block web crawlers. Try increasing the `--depth` to find alternative sources.
   - Example: `cliche research "Your query" --depth 5`

2. **Slow Response Times**:
   - Research with high depth values will take longer. Consider reducing depth for faster results.
   - Example: `cliche research "Quick answer needed" --depth 1`

3. **Content Quality Issues**:
   - If results are poor, try refining your query to be more specific
   - Example: `cliche research "Specific React hook usage examples"`

### Debug Mode

Enable debug mode to see details about the research process:

```bash
cliche research "Your query" --debug
```

This will show:
- Search results and URLs being processed
- Content extraction attempts and success rates
- Fallback mechanisms being employed
- Token usage and processing details

## Advanced Usage

### Combining with Other Commands

Research results can be used with other CLIche commands for more comprehensive workflows:

**Research to Scrape Pipeline:**
```bash
# First, research to find relevant sources
cliche research "Python asyncio tutorial" --debug

# Then scrape a specific source from the results
cliche scrape "https://realpython.com/async-io-python/" --topic "Python asyncio" --depth 2

# Finally, generate a comprehensive document
cliche generate "Python asyncio" --format markdown --professional
```

### Using the Bypass Environment

For testing or when encountering issues, you can use the bypass environment:

```bash
./cliche-bypass research "Your query" --debug
```

---

Made with ❤️ by Pink Pixel
Dream it, Pixel it ✨ 