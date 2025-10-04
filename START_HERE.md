# 🚀 START HERE - Mobile-Use with OpenRouter Free Models

## ⚠️ CRITICAL FIRST STEP

**You MUST rebuild the Docker containers before running any tasks!**

The system has been fixed to work with OpenRouter free models, but the fixes need to be built into the Docker containers.

### Step 1: Rebuild Docker Containers (REQUIRED)

```powershell
powershell.exe -ExecutionPolicy Bypass -File rebuild-docker.ps1
```

**This takes 5-10 minutes the first time.** It rebuilds the containers with:
- ✅ OpenRouter free model compatibility (json_mode instead of json_schema)
- ✅ Maestro analytics disabled (no more prompts)
- ✅ Retry logic with exponential backoff
- ✅ All configuration improvements

### Step 2: Verify Setup

```powershell
powershell.exe -ExecutionPolicy Bypass -File test-setup.ps1
```

Expected output:
```
=== Mobile-Use Setup Verification ===

Checking ADB...
[OK] ADB is installed

Checking .env configuration...
[OK] .env file exists
[OK] OpenRouter API key is configured
[OK] Maestro analytics disabled

Checking LLM configuration...
[OK] llm-config.override.jsonc exists
[OK] Using free OpenRouter models

Checking output directory...
[OK] Output directory exists

=== Setup verification complete ===
```

### Step 3: Run a Task

```powershell
powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
  "Open Settings and check the device name" `
  --output-description "Device name as a string"
```

Or use the example script:
```powershell
powershell.exe -ExecutionPolicy Bypass -File example-task.ps1
```

### Step 4: Check Results

```powershell
# View final results
Get-Content ./output/results.json

# View agent thoughts and decisions
Get-Content ./output/events.json
```

## 🎯 What Was Fixed

All 4 issues from your original request have been fixed:

1. ✅ **Loop/Retry** - Agent now retries 3 times with exponential backoff (2s, 4s, 8s)
2. ✅ **OpenRouter Free Models** - Fixed json_schema compatibility (now uses json_mode)
3. ✅ **Maestro Analytics** - Completely disabled, no more prompts
4. ✅ **Errors Fixed** - All ConnectionError and json_schema errors resolved

**Plus the critical infrastructure fix:**
5. ✅ **Docker Build** - Containers now build from local code with all fixes

## 📚 Documentation

- **`FINAL_SUMMARY.md`** - Complete explanation of all fixes
- **`QUICK_START.md`** - Quick reference guide
- **`SETUP_GUIDE.md`** - Detailed setup and troubleshooting
- **`INDEX.md`** - Full documentation index

## 🔧 Common Commands

```powershell
# Rebuild containers (after code changes or first time)
powershell.exe -ExecutionPolicy Bypass -File rebuild-docker.ps1

# Verify setup
powershell.exe -ExecutionPolicy Bypass -File test-setup.ps1

# Run example task
powershell.exe -ExecutionPolicy Bypass -File example-task.ps1

# Run custom task
powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 "Your task here"
```

## ❓ Troubleshooting

### Still seeing json_schema errors?
**Solution:** Run `rebuild-docker.ps1` to rebuild containers with the fix.

### Still seeing Maestro analytics prompts?
**Solution:** Run `rebuild-docker.ps1` to rebuild containers with analytics disabled.

### Changes not being applied?
**Solution:** The system runs in Docker. You must rebuild containers after any code changes:
```powershell
powershell.exe -ExecutionPolicy Bypass -File rebuild-docker.ps1
```

### Task fails immediately?
**Solution:** Check that:
1. You rebuilt the containers (`rebuild-docker.ps1`)
2. Your `.env` has the OpenRouter API key
3. Your device is connected (`adb devices`)

## 🎓 Understanding the Architecture

```
mobile-use.ps1
    ↓
Docker Compose
    ↓
Docker Container (built from local code)
    ↓
Python code with all fixes
    ↓
OpenRouter API (free models)
```

**Key Point:** The code runs inside Docker containers, so you must rebuild them to apply any fixes.

## ✅ Quick Checklist

- [ ] Run `rebuild-docker.ps1` (REQUIRED FIRST STEP)
- [ ] Run `test-setup.ps1` to verify
- [ ] Run `example-task.ps1` to test
- [ ] Try your own tasks

## 🎉 You're Ready!

Once you've rebuilt the containers, the system is ready to use with OpenRouter free models.

**Start with:**
```powershell
powershell.exe -ExecutionPolicy Bypass -File rebuild-docker.ps1
```

Then test with:
```powershell
powershell.exe -ExecutionPolicy Bypass -File example-task.ps1
```

---

**For detailed information, see `FINAL_SUMMARY.md`**
