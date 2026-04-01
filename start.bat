@echo off
title Stock Mirror Fish — Starting...
color 0A

echo.
echo  ============================================
echo    STOCK MIRROR FISH  ^|  Multi-Agent AI
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.10+
    echo  Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Navigate to script directory
cd /d "%~dp0"

:: Install dependencies
echo  Installing dependencies (first run may take ~1 minute)...
pip install -r requirements.txt --quiet --disable-pip-version-check
echo  Dependencies ready.
echo.

:: Open browser after short delay (background)
start "" /b cmd /c "timeout /t 4 /nobreak >nul && start http://localhost:8080"

:: Launch backend
echo  Starting server at http://localhost:8080
echo  (Your browser will open automatically)
echo.
echo  Press Ctrl+C to stop the server.
echo  ============================================
echo.

python app.py

echo.
echo  Server stopped. Press any key to close.
pause >nul
