# Test the Gmail task with the fixed code
Write-Host "=== Testing Mobile-Use with Fixed Code ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Running the Gmail task to verify all fixes are working..." -ForegroundColor White
Write-Host ""

powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 `
  "Open Gmail, find first 3 unread emails, and list their sender and subject line" `
  --output-description "A JSON list of objects, each with 'sender' and 'subject' keys"

