@echo off
REM SecureOps AI - Windows Startup Script

echo.
echo ========================================
echo  SecureOps AI - SOC Assistant Startup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
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
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo Warning: .env file not found
    if exist ".env.example" (
        echo Creating .env file from .env.example...
        copy ".env.example" ".env" >nul
        echo Please edit .env and add your API keys:
        echo   - GOOGLE_API_KEY (required)
        echo   - LANGSMITH_API_KEY (optional)
        echo.
    ) else (
        echo Error: .env.example not found
        echo Please ensure you are running this script from the project root directory.
        pause
        exit /b 1
    )
)

REM Start the application
echo.
echo ========================================
echo  Starting Streamlit application...
echo  The app will open at http://localhost:8501
echo ========================================
echo.

streamlit run src/app.py

REM Deactivate virtual environment on exit
deactivate
