$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "`nMinuteHire CareerVoice - Windows launcher" -ForegroundColor Cyan
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Setting up Python virtual environment..." -ForegroundColor Yellow
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Python 3.12 not found; trying the default Python 3 launcher..." -ForegroundColor Yellow
        py -3 -m venv .venv
    }
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        throw "Python environment creation failed. Install Python 3.12 and try again."
    }
}
& ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env - no key is required for offline demo mode." -ForegroundColor Green
}
Write-Host "Open http://127.0.0.1:8000 in Chrome or Edge" -ForegroundColor Green
& ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
