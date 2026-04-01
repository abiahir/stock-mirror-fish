# Stock Mirror Fish — PowerShell Launcher
# Right-click this file → "Run with PowerShell"

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $dir

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "    STOCK MIRROR FISH  |  Multi-Agent AI    " -ForegroundColor Green
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""

# Install deps
Write-Host "  Checking Python dependencies..." -ForegroundColor Yellow
pip install -r "$dir\requirements.txt" --quiet --disable-pip-version-check 2>&1 | Out-Null
Write-Host "  Dependencies ready." -ForegroundColor Green
Write-Host ""

# Open browser after 4 seconds (background job)
Start-Job -ScriptBlock {
    Start-Sleep 4
    Start-Process "http://localhost:8080"
} | Out-Null

Write-Host "  Starting server at http://localhost:8080" -ForegroundColor Green
Write-Host "  Browser will open automatically." -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

python "$dir\app.py"
