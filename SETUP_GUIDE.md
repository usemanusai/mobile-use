# Mobile-Use Setup Guide

## Recent Improvements

This guide documents the improvements made to the mobile-use system for better reliability and user experience.

### 1. Fixed OpenRouter Free Models Compatibility

**Problem**: OpenRouter free models don't support `json_schema` response format, causing errors like:
```
Input should be 'text', 'json', 'json_object' or 'structural_tag'
```

**Solution**: Modified `minitap/mobile_use/services/llm.py` to automatically use `json_mode` instead of `json_schema` for OpenRouter models. This ensures compatibility with free tier models like `deepseek/deepseek-chat-v3.1:free`.

### 2. Disabled Maestro Analytics Prompts

**Problem**: Maestro CLI would prompt for analytics consent on every run:
```
[Maestro Studio]: Maestro CLI would like to collect anonymous usage data to improve the product.
[Maestro Studio]: Enable analytics? [Y/n]
```

**Solution**: 
- Added environment variables to disable analytics in `minitap/mobile_use/servers/device_hardware_bridge.py`
- Filtered out analytics messages from stdout
- Added `MAESTRO_DISABLE_ANALYTICS=true` to `.env` file

### 3. Added Retry Logic with Exponential Backoff

**Problem**: Agent would fail immediately on LLM errors without retrying.

**Solution**: Added retry logic to all agent nodes (Planner, Orchestrator, Cortex) with:
- 3 retry attempts
- Exponential backoff (2s, 4s, 8s)
- Detailed logging of retry attempts

This makes the system much more resilient to temporary API issues.

### 4. Improved Configuration

**Changes to `.env`**:
- Fixed output paths to use relative paths (`./output/`)
- Added Maestro analytics disable flags
- Better organized with comments

## Quick Start

### Prerequisites

1. **Android Device/Emulator**: Connected via ADB
2. **Maestro CLI**: Installed and in PATH
3. **OpenRouter API Key**: Get one from https://openrouter.ai/

### Setup Steps

1. **Clone and navigate to the project**:
   ```bash
   cd mobile-use-2.3.0
   ```

2. **Configure your API key**:
   Edit `.env` and add your OpenRouter API key:
   ```
   OPEN_ROUTER_API_KEY=your-key-here
   ```

3. **Configure LLM models** (already done for free models):
   The `llm-config.override.jsonc` is already configured to use free OpenRouter models:
   - Planner: `deepseek/deepseek-chat-v3.1:free`
   - Orchestrator: `deepseek/deepseek-chat-v3.1:free`
   - Cortex: `deepseek/deepseek-chat-v3.1:free`
   - Executor: `deepseek/deepseek-chat-v3.1:free`
   - Hopper: `qwen/qwen3-coder:free`
   - Outputter: `deepseek/deepseek-chat-v3.1:free`

4. **Connect your Android device**:
   ```bash
   adb devices
   ```

5. **Run a task**:
   ```powershell
   powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
     "Open Gmail, find first 3 unread emails, and list their sender and subject line" `
     --output-description "A JSON list of objects, each with 'sender' and 'subject' keys"
   ```

## Using Free OpenRouter Models

The system is now optimized for free OpenRouter models. Here are some tips:

### Recommended Free Models

1. **DeepSeek Chat v3.1** (`deepseek/deepseek-chat-v3.1:free`)
   - Good for general reasoning tasks
   - Used for: Planner, Orchestrator, Cortex, Executor, Outputter

2. **Qwen3 Coder** (`qwen/qwen3-coder:free`)
   - Good for code and structured data
   - Used for: Hopper (requires 256k context)

### Rate Limits

Free models have rate limits. The retry logic will help handle temporary failures:
- First retry: 2 seconds
- Second retry: 4 seconds
- Third retry: 8 seconds

If you hit rate limits frequently, consider:
1. Reducing task complexity
2. Breaking tasks into smaller steps
3. Upgrading to paid models

## Troubleshooting

### Issue: "json_schema" error
**Status**: ✅ Fixed
This should no longer occur with the updated code.

### Issue: Maestro analytics prompt
**Status**: ✅ Fixed
Analytics are now disabled by default.

### Issue: Agent stops on first error
**Status**: ✅ Fixed
Retry logic now handles temporary failures.

### Issue: Connection errors
**Solution**: 
- Check your internet connection
- Verify your OpenRouter API key
- Check if you've hit rate limits (wait a few minutes)

### Issue: Device not found
**Solution**:
```bash
# For Android
adb devices
adb tcpip 5555
adb connect <device-ip>:5555

# For iOS
xcrun simctl list devices
```

## Output Files

Results are saved to:
- `./output/events.json` - Agent thoughts and decisions
- `./output/results.json` - Final structured output

## Advanced Configuration

### Custom Models

Edit `llm-config.override.jsonc` to use different models:

```jsonc
{
  "planner": {
    "provider": "openrouter",
    "model": "your-model-here"
  }
  // ... other agents
}
```

### Retry Configuration

To modify retry behavior, edit the agent files:
- `minitap/mobile_use/agents/planner/planner.py`
- `minitap/mobile_use/agents/orchestrator/orchestrator.py`
- `minitap/mobile_use/agents/cortex/cortex.py`

Look for:
```python
max_retries = 3  # Change this
retry_delay = 2  # Change this
```

## Performance Tips

1. **Use specific, clear goals**: The more specific your task description, the better the results
2. **Break complex tasks into steps**: Instead of one complex task, run multiple simpler tasks
3. **Monitor output files**: Check `./output/events.json` to see agent reasoning
4. **Adjust max_steps**: For complex tasks, increase the step limit

## Support

For issues or questions:
1. Check the logs in the terminal
2. Review `./output/events.json` for agent thoughts
3. Verify your configuration in `.env` and `llm-config.override.jsonc`

## Summary of Changes

| File | Changes |
|------|---------|
| `minitap/mobile_use/services/llm.py` | Added json_mode support for OpenRouter |
| `minitap/mobile_use/servers/device_hardware_bridge.py` | Disabled Maestro analytics |
| `minitap/mobile_use/agents/planner/planner.py` | Added retry logic |
| `minitap/mobile_use/agents/orchestrator/orchestrator.py` | Added retry logic |
| `minitap/mobile_use/agents/cortex/cortex.py` | Added retry logic |
| `.env` | Fixed paths, added analytics disable |
| `.gitignore` | Added output directory |

All changes are backward compatible and improve system reliability.

