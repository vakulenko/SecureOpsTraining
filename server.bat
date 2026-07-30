@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo  SecureOps AI - Local Agent Server
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

REM Install FastAPI and Uvicorn
echo Installing FastAPI and Uvicorn...
pip install fastapi uvicorn --quiet

REM Create .env from .env.example if needed
if not exist ".env" (
    echo.
    if exist ".env.example" (
        echo Creating .env file from template...
        copy ".env.example" ".env" >nul
        echo.
        echo Note: Please verify your API keys are set in .env:
        echo   - GOOGLE_API_KEY (required for Gemini API)
        echo   - LANGSMITH_API_KEY (required for tracing)
        echo   - LANGSMITH_TRACING=true (for tracing)
        echo.
    )
)

REM Display server information
echo.
echo ========================================
echo  LOCAL AGENT SERVER STARTED
echo ========================================
echo.
echo Server Information:
echo   URL: http://localhost:8000
echo   Status: http://localhost:8000/health
echo.
echo How to connect to LangSmith Studio:
echo   1. Open LangSmith Studio in your browser
echo   2. Click "Configure Studio connection"
echo   3. Enter Base URL: http://localhost:8000
echo   4. Click "Connect"
echo.
echo Once connected, you can:
echo   - See real-time agent execution flow
echo   - View graph structure and routing
echo   - Monitor state changes at each node
echo   - Debug agent behavior visually
echo.
echo Keep this window open while using Studio.
echo.
echo ========================================
echo.

REM Start the server
python src\server.py

REM Handle errors
if errorlevel 1 (
    echo.
    echo Error: Failed to start server
    echo Troubleshooting:
    echo   - Check that src/server.py exists
    echo   - Check that src/graph.py is valid
    echo   - Try: pip install -U fastapi uvicorn
    echo.
    pause
)
