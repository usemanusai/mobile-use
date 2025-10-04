# Example task script for mobile-use
# This demonstrates a simple task that should work on any Android device

Write-Host "=== Mobile-Use Example Task ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will run a simple task to test the mobile-use system." -ForegroundColor White
Write-Host "Task: Open Settings and get the device name" -ForegroundColor White
Write-Host ""

# Check if device is connected
Write-Host "Checking for connected devices..." -ForegroundColor Yellow
$devices = adb devices
Write-Host $devices -ForegroundColor Gray

if ($devices -match "device$") {
    Write-Host "[OK] Device found!" -ForegroundColor Green
} else {
    Write-Host "[FAIL] No device found. Please connect a device and try again." -ForegroundColor Red
    Write-Host ""
    Write-Host "To connect a device:" -ForegroundColor Yellow
    Write-Host "  adb devices" -ForegroundColor Gray
    Write-Host "  adb tcpip 5555" -ForegroundColor Gray
    Write-Host "  adb connect <device-ip>:5555" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "Starting task..." -ForegroundColor Yellow
Write-Host ""

# Run the task
powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
  "Open Settings and check the device name" `
  --output-description "Device name as a string"

Write-Host ""
Write-Host "=== Task Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check the results:" -ForegroundColor White
Write-Host "  - Agent thoughts: ./output/events.json" -ForegroundColor Gray
Write-Host "  - Final output: ./output/results.json" -ForegroundColor Gray
Write-Host ""

# Show results if they exist
if (Test-Path "./output/results.json") {
    Write-Host "Results:" -ForegroundColor Green
    Get-Content "./output/results.json"
    Write-Host ""
}

Write-Host "For more examples, see QUICK_START.md" -ForegroundColor Cyan
