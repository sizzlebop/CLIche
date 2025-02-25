#!/bin/bash
# Test the enhanced essay format with clickable references at the bottom

echo "=== Testing Enhanced Essay Format with Clickable References ==="
echo

# Test with a simple research query that will produce comprehensive results
echo "Generating enhanced research document in essay format..."
./cliche-bypass research "Benefits of meditation" --depth 3 --fallback-only --write --format markdown

# Check if successful
if [ $? -eq 0 ]; then
  echo "✅ Document generated successfully!"
  
  # Find the generated file
  DOCS_DIR="${HOME}/.cliche/files/docs"
  LATEST_FILE=$(ls -t "$DOCS_DIR" | grep -i "research_benefits_of" | head -n 1)
  
  if [ -n "$LATEST_FILE" ]; then
    echo "✅ Generated document: $DOCS_DIR/$LATEST_FILE"
    
    # Check document length to ensure it's comprehensive
    WORD_COUNT=$(wc -w < "$DOCS_DIR/$LATEST_FILE")
    echo "📊 Document word count: $WORD_COUNT words"
    
    if [ $WORD_COUNT -gt 1000 ]; then
      echo "✅ Document is comprehensive with more than 1000 words"
    else
      echo "⚠️ Document may not be as comprehensive as expected (less than 1000 words)"
    fi
    
    # Check if it has a References section
    if grep -q "## References" "$DOCS_DIR/$LATEST_FILE"; then
      echo "✅ Document contains a References section as expected"
      
      # Check for citation format [1]
      if grep -q "\[[0-9]\]" "$DOCS_DIR/$LATEST_FILE"; then
        echo "✅ Document uses numbered citations as expected"
      else
        echo "❌ Document doesn't appear to use numbered citations"
      fi
      
      # Check for clickable references with markdown links
      if grep -q "\[.*\](http" "$DOCS_DIR/$LATEST_FILE"; then
        echo "✅ Document contains clickable references as expected"
      else
        echo "❌ Document doesn't appear to have clickable references"
      fi
      
      # Check for multiple sections (headers)
      SECTION_COUNT=$(grep -c "^##" "$DOCS_DIR/$LATEST_FILE")
      echo "📊 Document section count: $SECTION_COUNT sections"
      
      if [ $SECTION_COUNT -ge 5 ]; then
        echo "✅ Document has at least 5 sections as expected"
      else
        echo "⚠️ Document has fewer sections than expected (less than 5)"
      fi
      
      echo
      echo "Document structure preview:"
      echo "================================"
      # Show the headings structure
      grep "^#" "$DOCS_DIR/$LATEST_FILE"
      echo "================================"
      
      echo
      echo "References section preview:"
      echo "================================"
      # Extract the References section
      sed -n '/## References/,$p' "$DOCS_DIR/$LATEST_FILE" | head -10
      echo "================================"
      
    else
      echo "❌ Document doesn't contain a References section"
    fi
  else
    echo "❌ Cannot find the generated document"
  fi
else
  echo "❌ Document generation failed"
fi

echo
echo "=== Test completed ===" 