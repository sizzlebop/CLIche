#!/bin/bash
# Helper script for scraping with multi-word topics

# Check if URL is provided
if [ $# -lt 2 ]; then
  echo "Usage: ./scrape.sh <URL> <TOPIC> [depth] [max_pages] [--no-llm]"
  echo "Example: ./scrape.sh https://docs.github.com 'GitHub Copilot Pro'"
  echo "Example with no LLM: ./scrape.sh https://docs.github.com 'GitHub Copilot Pro' 2 5 --no-llm"
  exit 1
fi

# Get parameters
URL="$1"
TOPIC="$2"
DEPTH="${3:-1}"  # Default to 1 if not provided
MAX_PAGES="${4:-3}"  # Default to 3 if not provided
NO_LLM_FLAG=""

# Check for no-llm flag
if [[ "$*" == *--no-llm* ]]; then
  NO_LLM_FLAG="--no-llm"
fi

# Run the command with properly quoted topic
echo "🔍 Scraping for topic: '$TOPIC'"
echo "📚 Command: ./cliche-bypass scrape \"$URL\" --topic \"$TOPIC\" --depth $DEPTH --max-pages $MAX_PAGES $NO_LLM_FLAG"
./cliche-bypass scrape "$URL" --topic "$TOPIC" --depth $DEPTH --max-pages $MAX_PAGES $NO_LLM_FLAG 