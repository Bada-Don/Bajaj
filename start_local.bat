@echo off
echo Starting Document Search API for local development...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found
    echo Please create a .env file with your API keys
    echo.
    echo Example .env file:
    echo GOOGLE_API_KEY=your_google_api_key
    echo DATABASE_URL=sqlite:///./test.db
    echo PORT=8000
    echo.
)

REM Install dependencies if needed
echo Checking dependencies...
echo Installing Windows-compatible dependencies...
pip install -r requirements_windows.txt

echo.
echo Starting server...
echo Press Ctrl+C to stop
echo.

REM Start the application
python run_local.py

pause 