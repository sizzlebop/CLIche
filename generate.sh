#!/bin/bash
# Helper script for generating documents with multi-word topics

# Check if topic is provided
if [ $# -lt 1 ]; then
  echo "Usage: ./generate.sh <TOPIC> [format] [--raw]"
  echo "Example: ./generate.sh 'GitHub Copilot Pro' html"
  echo "Example with raw output: ./generate.sh 'Python async' markdown --raw"
  exit 1
fi

# Get parameters
TOPIC="$1"
FORMAT="${2:-markdown}"  # Default to markdown if not provided
RAW_FLAG=""

# Check for raw flag
if [[ "$*" == *--raw* ]]; then
  RAW_FLAG="--raw"
fi

# Run the command with properly quoted topic
echo "📝 Generating document for topic: '$TOPIC'"
echo "📚 Command: ./cliche-bypass generate \"$TOPIC\" --format $FORMAT $RAW_FLAG"
./cliche-bypass generate "$TOPIC" --format $FORMAT $RAW_FLAG 