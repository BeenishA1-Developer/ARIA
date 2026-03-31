@echo off
setlocal enabledelayedexpansion
title ARIA - Advanced AI Blogging Agent 🤖
color 0B
cd /d "%~dp0AutoBlog_Agent"

echo ====================================================
echo   ARIA: AI-Powered SEO and Blogging Pro Manager
echo ====================================================
echo.
echo [STATUS] Starting Web Interface...
echo [INFO] Persistent data loaded from ./data
echo [INFO] Live logs available in UI sidebar.
echo.

:: Start ARIA using local venv
if exist "venv\Scripts\python.exe" (
    echo [INFO] Checking dependencies...
    venv\Scripts\python.exe -c "import flask, flask_cors, groq" 2>nul
    if errorlevel 1 (
        echo [WARN] Missing dependencies! Installing now...
        venv\Scripts\python.exe -m pip install flask flask-cors requests beautifulsoup4 lxml loguru python-dotenv schedule groq google-generativeai
    )
    venv\Scripts\python.exe app.py
) else (
    echo [ERROR] Virtual environment 'venv' missing!
    echo Please wait, finishing setup...
    python -m venv venv
    venv\Scripts\python.exe -m pip install flask flask-cors requests beautifulsoup4 lxml loguru python-dotenv schedule groq google-generativeai
    venv\Scripts\python.exe app.py
)

if errorlevel 1 (
    echo.
    echo [CRITICAL ERROR] The agent failed to start.
    echo Please check if you have Python installed and if there's an internet connection.
    pause
)

pause
