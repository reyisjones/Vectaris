@echo off
REM Run Vectaris locally without Docker (Windows).
REM Backend on :8000, frontend on :5173. Close the spawned windows to stop.
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"

where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Install Python 3.10+ and re-run.
    exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
    echo npm not found. Install Node.js 20+ and re-run.
    exit /b 1
)

REM ---------- backend ----------
cd /d "%BACKEND_DIR%"
if not exist ".venv" (
    echo ==^> Creating Python virtual environment
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo ==^> Installing backend dependencies
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt -r requirements-dev.txt
if not exist ".env" copy /Y .env.example .env >nul

echo ==^> Starting backend on http://localhost:8000
start "Vectaris Backend" cmd /k "cd /d %BACKEND_DIR% && call .venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM ---------- frontend ----------
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo ==^> Installing frontend dependencies
    call npm install --no-audit --no-fund
)

echo ==^> Starting frontend on http://localhost:5173
start "Vectaris Frontend" cmd /k "cd /d %FRONTEND_DIR% && npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo Backend : http://localhost:8000  (docs: /docs, metrics: /metrics)
echo Frontend: http://localhost:5173
echo Close the spawned windows to stop the services.
endlocal
