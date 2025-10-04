# Rebuild Docker containers with local code changes
Write-Host "=== Rebuilding Mobile-Use Docker Containers ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will rebuild the Docker containers with your local code changes." -ForegroundColor White
Write-Host "This is necessary after modifying any Python files." -ForegroundColor White
Write-Host ""

# Stop any running containers
Write-Host "Stopping any running containers..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null

# Remove old images to force rebuild
Write-Host "Removing old images..." -ForegroundColor Yellow
docker-compose rm -f mobile-use-full-ip mobile-use-full-usb 2>&1 | Out-Null

# Build the containers (force no cache to ensure code changes are included)
Write-Host "Building containers with --no-cache (this may take a few minutes)..." -ForegroundColor Yellow
Write-Host ""

docker-compose build --no-cache mobile-use-full-ip

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Build Complete ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "The Docker containers have been rebuilt with your local code changes." -ForegroundColor White
    Write-Host ""
    Write-Host "You can now run tasks with:" -ForegroundColor White
    Write-Host "  powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1 'Your task here'" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "=== Build Failed ===" -ForegroundColor Red
    Write-Host ""
    Write-Host "There was an error building the Docker containers." -ForegroundColor Red
    Write-Host "Please check the error messages above." -ForegroundColor Red
    Write-Host ""
    exit 1
}

