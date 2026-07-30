@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo  SecureOps AI - SOC Assistant Startup
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Create .env from .env.example if needed
if not exist ".env" (
    echo.
    if exist ".env.example" (
        echo Creating .env file from template...
        copy ".env.example" ".env" >nul
        echo.
        echo Note: Please edit .env and add your API keys:
        echo   - GOOGLE_API_KEY (required for Gemini API)
        echo   - LANGSMITH_API_KEY (optional, for tracing)
        echo.
    )
)

REM Start the application
echo ========================================
echo Starting Streamlit application...
echo App will open at http://localhost:8501
echo ========================================
echo.

streamlit run src/app.py

REM Keep window open if there was an error
if errorlevel 1 (
    pause
)
