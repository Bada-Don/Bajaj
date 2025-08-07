# PowerShell script to start Document Search API on Windows
Write-Host "Starting Document Search API for local development..." -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found" -ForegroundColor Yellow
    Write-Host "Please create a .env file with your API keys" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Example .env file:" -ForegroundColor Cyan
    Write-Host "GOOGLE_API_KEY=your_google_api_key" -ForegroundColor Gray
    Write-Host "DATABASE_URL=sqlite:///./test.db" -ForegroundColor Gray
    Write-Host "PORT=8000" -ForegroundColor Gray
    Write-Host ""
}

# Install dependencies
Write-Host "Installing Windows-compatible dependencies..." -ForegroundColor Cyan
try {
    pip install -r requirements_windows.txt
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Error installing dependencies. Trying alternative method..." -ForegroundColor Yellow
    try {
        python -m pip install -r requirements_windows.txt
        Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install dependencies. Please check your Python installation." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "Starting server..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start the application
try {
    python run_local.py
} catch {
    Write-Host "Error starting the application. Please check the logs above." -ForegroundColor Red
}

Read-Host "Press Enter to exit" 