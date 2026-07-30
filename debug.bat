@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo  SecureOps AI - Debug Mode with LangSmith
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
        echo Note: Please verify your API keys are set in .env:
        echo   - GOOGLE_API_KEY (required for Gemini API)
        echo   - LANGSMITH_API_KEY (required for tracing)
        echo.
    )
)

REM Display debug mode information
echo.
echo ========================================
echo  DEBUG MODE CONFIGURATION
echo ========================================
echo.
echo Features enabled:
echo   - LangSmith Tracing (View traces in Studio)
echo   - Debug Logging (Verbose output in console)
echo   - Real-time Agent Monitoring
echo.

REM Check if LangSmith is configured
if exist ".env" (
    for /f "tokens=2 delims==" %%A in ('findstr /R "LANGSMITH_TRACING" .env') do set LANGSMITH_TRACING=%%A
    for /f "tokens=2 delims==" %%A in ('findstr /R "LANGSMITH_PROJECT" .env') do set LANGSMITH_PROJECT=%%A

    if "!LANGSMITH_TRACING!"=="true" (
        echo ✅ LangSmith Tracing: ENABLED
        if not "!LANGSMITH_PROJECT!"=="" (
            echo ✅ Project: !LANGSMITH_PROJECT!
            echo.
            echo 📈 Opening LangSmith Studio in browser...
            timeout /t 2 /nobreak
            start https://smith.langchain.com/projects/!LANGSMITH_PROJECT!
        )
    ) else (
        echo ⏸️  LangSmith Tracing: DISABLED
        echo To enable, set LANGSMITH_TRACING=true in .env
    )
) else (
    echo ⚠️  .env file not found
    echo Please ensure .env is configured with API keys
)

echo.
echo ========================================
echo Starting Streamlit in DEBUG mode...
echo App will open at http://localhost:8501
echo ========================================
echo.
echo Tip: Open LangSmith Studio to view traces
echo      as you interact with the application.
echo.

REM Enable debug mode and run Streamlit
set DEBUG=true
set STREAMLIT_LOGGER_LEVEL=debug

streamlit run src/app.py --logger.level=debug

REM Keep window open if there was an error
if errorlevel 1 (
    pause
)
