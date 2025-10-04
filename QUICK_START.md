# Quick Start Guide

## ⚠️ IMPORTANT: First Time Setup

**Before running any tasks, you MUST rebuild the Docker containers:**

```powershell
powershell.exe -ExecutionPolicy Bypass -File rebuild-docker.ps1
```

This rebuilds the containers with all the fixes for OpenRouter free models. This takes 5-10 minutes the first time.

## Prerequisites Check

After rebuilding, verify your setup:
```powershell
powershell.exe -ExecutionPolicy Bypass -File test-setup.ps1
```

## Basic Usage

### Simple Task
```powershell
powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
  "Open Settings and check the device name"
```

### Task with Structured Output
```powershell
powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
  "Open Gmail, find first 3 unread emails, and list their sender and subject line" `
  --output-description "A JSON list of objects, each with 'sender' and 'subject' keys"
```

## Configuration Files

### `.env` - API Keys and Settings
```bash
OPEN_ROUTER_API_KEY=your-key-here
EVENTS_OUTPUT_PATH=./output/events.json
RESULTS_OUTPUT_PATH=./output/results.json
MAESTRO_DISABLE_ANALYTICS=true
```

### `llm-config.override.jsonc` - Model Selection
```jsonc
{
  "planner": {
    "provider": "openrouter",
    "model": "deepseek/deepseek-chat-v3.1:free"
  },
  "orchestrator": {
    "provider": "openrouter",
    "model": "deepseek/deepseek-chat-v3.1:free"
  },
  "cortex": {
    "provider": "openrouter",
    "model": "deepseek/deepseek-chat-v3.1:free",
    "fallback": {
      "provider": "openrouter",
      "model": "deepseek/deepseek-chat-v3.1:free"
    }
  },
  "executor": {
    "provider": "openrouter",
    "model": "deepseek/deepseek-chat-v3.1:free"
  },
  "utils": {
    "hopper": {
      "provider": "openrouter",
      "model": "qwen/qwen3-coder:free"
    },
    "outputter": {
      "provider": "openrouter",
      "model": "deepseek/deepseek-chat-v3.1:free"
    }
  }
}
```

## Output Files

Results are saved to:
- `./output/events.json` - Agent thoughts and decisions
- `./output/results.json` - Final structured output

## Common Tasks

### Email Tasks
```powershell
# List unread emails
powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
  "Open Gmail and count unread emails" `
  --output-description "Number of unread emails"

# Read specific email
powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
  "Open Gmail, find email from John, and extract the subject" `
  --output-description "Email subject as string"
```

### Settings Tasks
```powershell
# Check device info
powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
  "Open Settings, go to About Phone, and get device name and Android version" `
  --output-description "JSON with 'device_name' and 'android_version' keys"

# Check WiFi
powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
  "Open Settings, check if WiFi is enabled" `
  --output-description "Boolean: true if WiFi is on, false otherwise"
```

### App Tasks
```powershell
# Open app and extract data
powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
  "Open Calculator app and verify it's running" `
  --output-description "App status as string"
```

## Troubleshooting

### Issue: "json_schema" error
**Status:** ✅ Fixed - Should not occur anymore

### Issue: Maestro analytics prompt
**Status:** ✅ Fixed - Analytics disabled by default

### Issue: Connection errors
**Solution:** Check internet and API key, wait if rate limited

### Issue: Device not found
**Solution:**
```bash
adb devices
adb tcpip 5555
adb connect <device-ip>:5555
```

## Tips for Best Results

1. **Be Specific**: Clear, detailed task descriptions work best
2. **Break Down Complex Tasks**: Multiple simple tasks > one complex task
3. **Use Structured Output**: Specify exact JSON format you want
4. **Monitor Logs**: Check `./output/events.json` to see agent reasoning
5. **Adjust Steps**: For complex tasks, increase max_steps if needed

## Free Model Limits

OpenRouter free models have rate limits:
- If you hit limits, wait a few minutes
- Retry logic will handle temporary failures (3 attempts)
- Consider upgrading to paid models for heavy usage

## Getting Help

1. Run `test-setup.ps1` to verify configuration
2. Check `SETUP_GUIDE.md` for detailed troubleshooting
3. Review `./output/events.json` for agent thoughts
4. Check terminal output for error messages

## Example Session

```powershell
# 1. Verify setup
PS> powershell.exe -ExecutionPolicy Bypass -File test-setup.ps1
[OK] ADB is installed
[OK] OpenRouter API key is configured
[OK] Using free OpenRouter models
...

# 2. Run a simple task
PS> powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
      "Open Settings and get device name" `
      --output-description "Device name as string"

# 3. Check results
PS> Get-Content ./output/results.json
{"device_name": "Samsung Galaxy S21"}

# 4. Review agent thoughts
PS> Get-Content ./output/events.json
[
  "Opening Settings app...",
  "Navigating to About Phone...",
  "Found device name: Samsung Galaxy S21"
]
```

## What's New

Recent improvements:
- ✅ Fixed OpenRouter free models compatibility
- ✅ Removed Maestro analytics prompts
- ✅ Added retry logic for better reliability
- ✅ Improved error handling and logging

See `CHANGELOG.md` for full details.

---

**Ready to start?** Run `test-setup.ps1` first, then try a simple task!
