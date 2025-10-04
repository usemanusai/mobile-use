param(
  [string]$RepoName = 'mobile-use'
)

$ErrorActionPreference = 'Stop'
if (-not $env:GITHUB_TOKEN) { throw 'GITHUB_TOKEN env var is required' }
$headers = @{
  Authorization = "token $($env:GITHUB_TOKEN)"
  Accept        = 'application/vnd.github+json'
  'User-Agent'  = 'augment-agent'
}
$body = @{ name = $RepoName; description = 'Mobile-Use: AI-powered multi-agent system'; private = $false } | ConvertTo-Json
$response = Invoke-RestMethod -Method POST -Headers $headers -Body $body -ContentType 'application/json' -Uri 'https://api.github.com/user/repos'
$response | ConvertTo-Json -Compress | Write-Output

