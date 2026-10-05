@echo off
setlocal

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    set PYTHON=venv\Scripts\python
) else (
    set PYTHON=python
)

set EM_DB=data\demo.db

if not exist "%EM_DB%" (
    echo Demo database not found. Creating it now...
    %PYTHON% create_demo_db.py
    if errorlevel 1 (
        echo ERROR: Failed to create demo database.
        pause
        exit /b 1
    )
)

echo Starting Expense Monitor (DEMO) at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.

%PYTHON% -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

endlocal
