@echo off
setlocal

REM Activate venv if present, otherwise use system Python
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    set PYTHON=venv\Scripts\python
) else (
    set PYTHON=python
)

echo Starting Expense Monitor at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.

%PYTHON% -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

endlocal
