@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt --quiet
pip install langgraph-cli --quiet

python debug.py

pause
