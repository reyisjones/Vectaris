@echo off
REM Run Vectaris with Docker Compose (Windows).
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker not found. Install Docker Desktop first.
    exit /b 1
)
docker compose version >nul 2>nul
if errorlevel 1 (
    echo docker compose plugin not found. Install Docker Desktop or compose v2.
    exit /b 1
)

if not exist "backend\.env" copy /Y "backend\.env.example" "backend\.env" >nul

echo ==^> Building and starting containers
docker compose up --build %*

endlocal
