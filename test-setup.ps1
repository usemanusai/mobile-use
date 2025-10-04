# Test script to verify mobile-use setup
Write-Host "=== Mobile-Use Setup Verification ===" -ForegroundColor Cyan
Write-Host ""

# Check ADB
Write-Host "Checking ADB..." -ForegroundColor Yellow
try {
    adb version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] ADB is installed" -ForegroundColor Green
        adb devices
    } else {
        Write-Host "[FAIL] ADB not found" -ForegroundColor Red
    }
} catch {
    Write-Host "[FAIL] ADB not found in PATH" -ForegroundColor Red
}
Write-Host ""

# Check Maestro
Write-Host "Checking Maestro..." -ForegroundColor Yellow
try {
    maestro --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Maestro is installed" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Maestro not found" -ForegroundColor Red
    }
} catch {
    Write-Host "[FAIL] Maestro not found in PATH" -ForegroundColor Red
}
Write-Host ""

# Check .env file
Write-Host "Checking .env configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "[OK] .env file exists" -ForegroundColor Green
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "OPEN_ROUTER_API_KEY=sk-") {
        Write-Host "[OK] OpenRouter API key is configured" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] OpenRouter API key not configured" -ForegroundColor Red
    }
    if ($envContent -match "MAESTRO_DISABLE_ANALYTICS") {
        Write-Host "[OK] Maestro analytics disabled" -ForegroundColor Green
    }
} else {
    Write-Host "[FAIL] .env file not found" -ForegroundColor Red
}
Write-Host ""

# Check LLM config
Write-Host "Checking LLM configuration..." -ForegroundColor Yellow
if (Test-Path "llm-config.override.jsonc") {
    Write-Host "[OK] llm-config.override.jsonc exists" -ForegroundColor Green
    $llmConfig = Get-Content "llm-config.override.jsonc" -Raw
    if ($llmConfig -match "deepseek") {
        Write-Host "[OK] Using free OpenRouter models" -ForegroundColor Green
    }
} else {
    Write-Host "[FAIL] llm-config.override.jsonc not found" -ForegroundColor Red
}
Write-Host ""

# Check output directory
Write-Host "Checking output directory..." -ForegroundColor Yellow
if (Test-Path "output") {
    Write-Host "[OK] Output directory exists" -ForegroundColor Green
} else {
    New-Item -ItemType Directory -Force -Path "output" | Out-Null
    Write-Host "[OK] Output directory created" -ForegroundColor Green
}
Write-Host ""

Write-Host "=== Setup verification complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run a task:" -ForegroundColor White
Write-Host "  powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 'Your task here'" -ForegroundColor Green
Write-Host ""
Write-Host "See SETUP_GUIDE.md for more information" -ForegroundColor Cyan

