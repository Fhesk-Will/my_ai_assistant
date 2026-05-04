@echo off
title AI Assistant

echo ========================================
echo         AI Assistant - Starting...
echo ========================================
echo.

call C:\Users\12771\anaconda3\Scripts\activate.bat langchain
if errorlevel 1 (
    echo [FAIL] Cannot activate conda env: langchain
    pause
    exit /b 1
)
echo [OK] Conda env activated

cd /d "%~dp0"

start /b cmd /c "ping -n 3 127.0.0.1 >nul && start http://127.0.0.1:8888"

echo [OK] Starting server...
echo [OK] Browser will open http://127.0.0.1:8888
echo.
echo      Close this window to stop the server
echo ========================================
echo.
python server.py
