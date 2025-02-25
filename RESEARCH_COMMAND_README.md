# CLIche Research Command

## Overview

The CLIche Research command allows you to get up-to-date information from the web on any topic. It searches the internet, crawls relevant web pages, extracts content, and generates a comprehensive response based on the collected information.

Unlike the standard `ask` command, which relies solely on the LLM's pre-trained knowledge, the `research` command actively searches the web to provide you with current and factual information.

## Prerequisites

The research command requires the following Python packages:
- `duckduckgo-search` - For web searching
- `crawl4ai` - For web page content extraction
- `beautifulsoup4` - For fallback content extraction

Install these dependencies with:

```bash
pip install duckduckgo-search crawl4ai beautifulsoup4
```

## Usage

Basic usage:

```bash
cliche research "Your research question here"
```

With options:

```bash
cliche research "Current state of quantum computing" --depth 5
```

Generate a document:

```bash
cliche research "History of artificial intelligence" --write --format markdown
```

## Command Options

- `--depth`, `-d`: Number of search results to analyze (default: 3)
- `--debug`: Enable debug mode with detailed error messages
- `--fallback-only`: Skip primary crawler and use only the fallback scraper
- `--write`, `-w`: Generate a document instead of showing the response in the terminal
- `--format`, `-f`: Document format when using --write (choices: text, markdown, html; default: markdown)
- `--filename`: Optional filename for the generated document

## Examples

1. Research current events:
   ```bash
   cliche research "latest developments in AI regulation"
   ```

2. Get factual information:
   ```bash
   cliche research "health benefits of mediterranean diet"
   ```

3. Compare technologies:
   ```bash
   cliche research "React vs Vue.js 2023 comparison"
   ```

4. Generate a markdown document:
   ```bash
   cliche research "history of quantum computing" --write --format markdown
   ```

5. Generate an HTML document with a custom filename:
   ```bash
   cliche research "Space exploration milestones" --write --format html --filename space_exploration.html
   ```

6. Debug mode for troubleshooting:
   ```bash
   cliche research "quantum computing advances" --debug
   ```

## How It Works

1. The command searches the web using DuckDuckGo's search API
2. It crawls the top search results and extracts their content
   - First tries to use the `crawl4ai` library
   - Falls back to a simple BeautifulSoup-based scraper if needed
3. The extracted content is fed to the LLM along with your query
4. The LLM analyzes the information and generates a comprehensive response
5. Depending on the options:
   - Displays the response directly in your terminal (default)
   - OR generates a document in your specified format (with --write)

## Document Generation

When using the `--write` flag, the research command will:

1. Generate a comprehensive, in-depth document (1200-1500+ words) based on the research results
2. Structure it with a proper introduction, 5-7 distinct content sections, and conclusion
3. Use numbered citations (e.g., [1], [2]) in the text body for academic-style referencing
4. Include a dedicated "References" section at the end with properly formatted, clickable links to all sources
5. Save it to the `.cliche/files/docs/` directory by default
6. Use a filename derived from your query or the one you specified

The generated documents follow an academic/professional format that is:
- Thoroughly researched and detailed with comprehensive coverage of the topic
- Clean and easy to read without distracting inline links
- Properly structured with multiple distinct sections covering different aspects
- Formally cited with numbered references and clickable links at the bottom
- Perfect for research papers, reports, blog articles, or academic work

### Document Format Options

- **Markdown** (default): Comprehensive professional essay with rich markdown formatting and a References section with clickable links
- **HTML**: Clean HTML document with proper structure and a References section with clickable links
- **Text**: Plain text document with an essay structure and references with full URLs at the end

## Using with Bypass Script

If you're using the CLIche bypass script setup, you can run the research command with:

```bash
./cliche-bypass research "Your research question"
./cliche-bypass research "AI ethics" --write --format markdown
```

## Troubleshooting

- If you see an error about missing packages, install the required dependencies
- Use the `--debug` flag to get detailed error information 
- For optimal results, use a provider with a high context window (like Claude or GPT-4)
- If crawling fails for certain websites, try different search terms or increase the depth
- The command includes a fallback scraper that will attempt to extract content if the primary method fails
- If you're having issues with the primary crawler, use `--fallback-only` to rely on the more robust fallback scraper

## Notes

- Document generation is saved to `.cliche/files/docs/` by default
- Response quality depends on the search results and the LLM's ability to synthesize information
- Some websites may block web crawlers 
- Markdown format is the most versatile for most research documents 