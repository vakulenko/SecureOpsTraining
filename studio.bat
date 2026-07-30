@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo  LangGraph Local Studio Server
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

REM Install LangGraph CLI
echo Installing LangGraph CLI...
pip install langgraph-cli --quiet

REM Verify langgraph.json exists
if not exist "langgraph.json" (
    echo Error: langgraph.json not found in project root
    echo Please create langgraph.json with proper configuration
    pause
    exit /b 1
)

REM Display setup information
echo.
echo ========================================
echo  Local Studio Server Configuration
echo ========================================
echo.
echo LangGraph Configuration:
echo   File: langgraph.json
echo   Graph: soc_assistant
echo.
echo Server will start on:
echo   http://localhost:8023
echo.
echo How to use with LangSmith Studio:
echo   1. Keep this window open
echo   2. Open LangSmith Studio in your browser
echo   3. Click "Configure Studio connection"
echo   4. Enter Base URL: http://localhost:8023
echo   5. Click "Connect"
echo.
echo You'll then see:
echo   - Real-time graph execution visualization
echo   - State changes at each node
echo   - Agent flow and routing decisions
echo.
echo ========================================
echo Starting LangGraph Studio Server...
echo ========================================
echo.

REM Start the server
langgraph up

REM Handle errors
if errorlevel 1 (
    echo.
    echo Error: Failed to start LangGraph server
    echo Troubleshooting:
    echo   - Verify langgraph.json is correct
    echo   - Check that src/graph.py exists and is valid
    echo   - Try: pip install -U langgraph-cli
    pause
)
