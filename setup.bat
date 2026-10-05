@echo off
setlocal

echo ============================================================
echo  Expense Monitor — First-Time Setup
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/3] Installing dependencies (requires internet)...
venv\Scripts\pip install --upgrade pip --quiet
venv\Scripts\pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies. Check requirements.txt.
    pause
    exit /b 1
)

echo [3/3] Initialising database...
venv\Scripts\python -c "import database; database.init_db(); print('Database ready at:', database.DB_PATH)"
if errorlevel 1 (
    echo ERROR: Failed to initialise database.
    pause
    exit /b 1
)

echo.
echo Setup complete! Run the app with:  run.bat
echo.
pause
