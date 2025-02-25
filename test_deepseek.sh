#!/bin/bash
# Test DeepSeek API Integration

set -e  # Exit on error

echo "=== DeepSeek API Integration Test ==="
echo

# Step 1: Ensure we have a proper environment
echo "Step 1: Setting up Python environment..."
if [ -d "fresh_venv" ]; then
  source fresh_venv/bin/activate
else
  echo "Creating fresh virtual environment..."
  python3 -m venv fresh_venv
  source fresh_venv/bin/activate
  pip install -e .
  pip install requests
fi
echo "  Environment ready: $(which python)"
echo

# Step 2: Update the configuration file
echo "Step 2: Updating configuration..."
python update_config.py
echo

# Step 3: Test the DeepSeek API
echo "Step 3: Testing DeepSeek API..."
python test_deepseek_simple.py
TEST_RESULT=$?

# Report success or failure
echo 
if [ $TEST_RESULT -eq 0 ]; then
  echo "✅ Success! DeepSeek API integration is working."
else
  echo "❌ Error: DeepSeek API integration failed. Please check the error messages above."
fi

echo
echo "=== Test completed ===" 