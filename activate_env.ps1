# Market Sentiment Analysis Tool - Environment Activation Script
# This script automatically activates the market_sentiment uv environment

Write-Host "Market Sentiment Analysis Tool - Environment Setup" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Check if we're in the right directory
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# Check if environment exists
if (Test-Path ".\market_sentiment\Scripts\activate") {
    Write-Host "Activating market_sentiment environment..." -ForegroundColor Yellow
    & ".\market_sentiment\Scripts\activate"
    Write-Host "Environment activated successfully!" -ForegroundColor Green
    Write-Host "Python: " -NoNewline -ForegroundColor Cyan
    python --version
} else {
    Write-Host "Environment not found. Creating market_sentiment environment..." -ForegroundColor Yellow
    uv venv market_sentiment
    Write-Host "Environment created. Activating..." -ForegroundColor Yellow
    & ".\market_sentiment\Scripts\activate"
    Write-Host "Environment activated successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Ready for development! [ROCKET]" -ForegroundColor Green
Write-Host "- Backend: cd backend && python -m uvicorn main:app --reload" -ForegroundColor Cyan
Write-Host "- Frontend: cd frontend && npm run dev" -ForegroundColor Cyan
Write-Host "" 