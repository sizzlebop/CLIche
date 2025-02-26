# CLIche Research Command

The `research` command allows you to obtain up-to-date information from the web directly from your terminal. It leverages the power of search engines, smart web crawling, and LLM processing to provide comprehensive answers to your queries based on current information.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Options](#options)
- [Examples](#examples)
- [How It Works](#how-it-works)
- [Professional Mode](#professional-mode)
- [Automatic Unique File Naming](#automatic-unique-file-naming)
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
| `--image TEXT` | Add images related to the topic by search term |
| `--image-count INTEGER` | Number of images to add (default: 3) |
| `--image-width INTEGER` | Width of images in pixels (default: 800) |
| `--debug` | Enable debug mode for verbose output |
| `--help` | Show help message |

## Examples

**Basic research query:**
```bash
cliche research "Latest developments in quantum computing"
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

**Generate a research document with images:**
```bash
cliche research "National parks in the USA" --write --image "national parks" --image-count 4
```

**Professional research document with custom formatting and images:**
```bash
cliche research "Renewable energy technologies" --write --format html --professional --image "solar panels" --image-count 2
```

**Save research results to a markdown file:**
```bash
cliche research "Python best practices 2024" --write
```

**Use professional tone and save as HTML:**
```bash
cliche research "Business impact of AI" --professional --write --format html
```

**Add relevant images to your research document:**
```bash
cliche research "Climate change effects" --write --image "climate change" --image-count 3
```

**Customize output file name:**
```bash
cliche research "JavaScript frameworks comparison" --write --output js_frameworks_guide
```

**Combine multiple options:**
```bash
cliche research "Remote work productivity" --professional --write --format markdown --image "remote work" --image-count 2 --output remote_work_guide
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

## Document Generation Modes

When using the `--write` flag to generate a document, the research command leverages CLIche's advanced document generation capabilities:

### Comprehensive Documents (Default)

By default, the research command generates comprehensive documents that:

1. **Use Intelligent Chunking**: The system:
   - Extracts major sections from the researched content
   - Identifies natural section boundaries (headings, capitalized titles, etc.) 
   - Creates artificial sections when natural boundaries aren't found
   - Processes each section individually with the LLM to retain full detail
   - Combines sections into a cohesive document with proper structure

2. **Preserve Technical Depth**: All technical details, code examples, and explanations from the research are maintained.

3. **Handle Large Content Volumes**: By breaking content into manageable chunks, it can process much larger documents than would fit in a single LLM context window.

Example:
```bash
cliche research "Python asyncio programming" --write --format markdown
```

### Adding a Future Feature: Summary Mode

In an upcoming release, the research command will also support a `--summarize` flag (similar to the `generate` command) that will create more concise document summaries. This feature is currently in development.

## Image Integration with Direct URLs

When using the `--image` option with the `research` command, CLIche now embeds images with direct URLs from Unsplash instead of downloading them locally. This offers several advantages:

1. **Better compatibility** - Works with all markdown viewers and platforms
2. **Improved sharing** - Research documents can be shared without needing to include image files
3. **Standard compliance** - Uses standard markdown image syntax

The images are automatically placed at strategic locations within your research document (after introduction and major sections) to enhance the visual appeal and information value.

Example of using images with direct URLs in research:

```bash
cliche research "Renewable energy trends" --write --image "solar energy" --image-count 3
```

This will create a research document about renewable energy trends with three solar energy images embedded with direct Unsplash URLs, properly attributed in the document.

## Automatic Unique File Naming

The research command now implements automatic unique file naming to prevent overwriting existing files. When you generate multiple documents on the same topic:

- First document: `research_your_topic.md`
- Second document: `research_your_topic_1.md`
- Third document: `research_your_topic_2.md`

This allows you to:
- Generate multiple variations of research on the same topic for comparison
- Keep a history of your research
- Avoid accidentally overwriting previous work

All generated documents are stored in the `~/.cliche/files/docs/research/` directory for easy organization and access.

Example:
```bash
# Run twice to see the unique naming in action
cliche research "Space exploration" --write --format markdown
cliche research "Space exploration" --write --format markdown
```

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

**Research with Images Pipeline:**
```bash
# Research a topic with images and save as a document
cliche research "Deep sea creatures" --write --format markdown --image "deep sea animals" --image-count 3

# View the generated document
cliche view ~/cliche/files/docs/research/deep_sea_creatures.md
```

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