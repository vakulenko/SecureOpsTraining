@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  SecureOps AI - Complete Development Environment Setup
echo ============================================================
echo.
echo This script will help you start all components for full
echo debugging and monitoring with LangSmith and local Studio.
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

REM Create .env from .env.example if needed
if not exist ".env" (
    echo.
    if exist ".env.example" (
        echo Creating .env file from template...
        copy ".env.example" ".env" >nul
    )
)

REM Clear screen and show menu
cls
echo.
echo ============================================================
echo  SecureOps AI - Development Environment Launcher
echo ============================================================
echo.
echo Choose what you want to start:
echo.
echo 1) Full Development Environment (Recommended)
echo    - Streamlit app (http://localhost:8501)
echo    - Debug logging enabled
echo    - LangSmith Studio opens automatically
echo    - Local graph visualization available at localhost:8023
echo.
echo 2) Streamlit Only with Debug Logging
echo    - Streamlit app (http://localhost:8501)
echo    - Debug logging enabled
echo    - LangSmith Studio opens automatically
echo    - (No local graph server)
echo.
echo 3) Streamlit Normal Mode
echo    - Streamlit app (http://localhost:8501)
echo    - Clean interface, no debug output
echo    - Best for demos and stable work
echo.
echo 4) Local Graph Studio Server Only
echo    - LangGraph server (http://localhost:8023)
echo    - Use with "Configure Studio connection" dialog
echo    - Keep running while using other tools
echo.
echo 5) Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto full_dev
if "%choice%"=="2" goto debug_mode
if "%choice%"=="3" goto normal_mode
if "%choice%"=="4" goto studio_only
if "%choice%"=="5" goto exit_script

echo Invalid choice. Please try again.
timeout /t 2
goto :eof

:full_dev
echo.
echo Starting full development environment...
echo.
echo This will open:
echo   1. Terminal window (press Enter to continue)
echo   2. LangGraph Studio server (http://localhost:8023)
echo   3. Streamlit app (http://localhost:8501)
echo   4. LangSmith Studio (smith.langchain.com)
echo.
pause

echo.
echo Starting LangGraph server in new window...
timeout /t 1
start "LangGraph Studio Server" cmd /k "cd /d "%cd%" && call venv\Scripts\activate.bat && langgraph up"

timeout /t 3

echo Starting Streamlit in debug mode...
timeout /t 1
call venv\Scripts\activate.bat
set DEBUG=true
set STREAMLIT_LOGGER_LEVEL=debug
streamlit run src/app.py --logger.level=debug
goto :eof

:debug_mode
echo.
echo Starting Streamlit with debug logging...
echo LangSmith Studio will open automatically
echo.
call venv\Scripts\activate.bat
set DEBUG=true
set STREAMLIT_LOGGER_LEVEL=debug
streamlit run src/app.py --logger.level=debug
goto :eof

:normal_mode
echo.
echo Starting Streamlit in normal mode...
echo.
call venv\Scripts\activate.bat
streamlit run src/app.py
goto :eof

:studio_only
echo.
echo Starting LangGraph Studio server...
echo.
echo Server URL: http://localhost:8023
echo.
echo Keep this window open and use the URL in:
echo   LangSmith Studio ^> Configure Studio connection
echo.
call venv\Scripts\activate.bat
langgraph up
goto :eof

:exit_script
echo.
echo Exiting...
exit /b 0
