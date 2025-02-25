# DeepSeek API Troubleshooting

## The Problem

We identified that your DeepSeek API authentication was failing due to two issues:
1. The API key in your configuration was not set correctly
2. The model name in your configuration was incorrect

## How to Fix It

### Option 1: Use Our Automated Tool

1. Run the update_config.py script to automatically fix the configuration:
   ```bash
   python update_config.py
   ```

2. Test your configuration with the test script:
   ```bash
   python test_deepseek_simple.py
   ```

### Option 2: Manually Edit Your Config File

1. Open your CLIche configuration file:
   ```bash
   nano ~/.config/cliche/config.json
   ```

2. Find the DeepSeek section and replace the placeholder API key with your actual DeepSeek API key, and ensure the model name is `deepseek-chat`:
   ```json
   "deepseek": {
     "model": "deepseek-chat",
     "max_tokens": 2048,
     "api_key": "YOUR_ACTUAL_API_KEY_HERE",
     "api_base": "https://api.deepseek.com/v1"
   }
   ```

3. Save the file (Ctrl+O, Enter, Ctrl+X in nano)

### Option 3: Use Environment Variables

1. Set your DeepSeek API key as an environment variable:
   ```bash
   export DEEPSEEK_API_KEY=your_actual_api_key_here
   ```

2. Run CLIche commands with this environment variable set

## Verifying the Fix

After updating your API key and model, you can verify it's working with:

```bash
python test_deepseek_simple.py
# Or use the CLIche command
cliche roast me --provider deepseek
```

## Important Notes

- The model name must be `deepseek-chat` (not `deepseek-chat-v1` or other variants)
- Make sure your DeepSeek API key is valid
- The API base URL should be `https://api.deepseek.com/v1`
- Make sure your internet connection can reach the DeepSeek API servers

## Next Steps

Once the API key and model name issues are resolved, we can proceed with implementing the configuration wizard feature as originally planned.

## Config File Management

We've added a config manager utility to automatically create and manage your configuration file. You can use the `ensure_config.py` script to:

1. Check if your config exists
2. Create a default config if it doesn't
3. Backup your existing config

This prevents the accidental loss of your API keys in the future. 