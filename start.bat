@echo off
title A2 Intelligence Risk Analytics Platform
echo.
echo  ============================================
echo   A2 Intelligence Risk Analytics Platform
echo   by AA Impact Inc.
echo  ============================================
echo.

:: ── Configuration ──────────────────────────────────────────────────────────────
set PROJECT_ROOT=%~dp0
set BACKEND_DIR=%PROJECT_ROOT%backend
set FRONTEND_DIR=%PROJECT_ROOT%frontend
set BACKEND_PORT=8001
set FRONTEND_PORT=3000

:: ── Pre-flight checks ──────────────────────────────────────────────────────────
echo [1/4] Checking prerequisites...

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo  ERROR: Python not found. Install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo  ERROR: Node.js not found. Install Node.js 18+ and add to PATH.
    pause
    exit /b 1
)

:: ── Check backend .env ──────────────────────────────────────────────────────────
if not exist "%BACKEND_DIR%\.env" (
    echo  ERROR: backend\.env not found. Copy .env.example and configure DATABASE_URL.
    pause
    exit /b 1
)

:: ── Check frontend node_modules ─────────────────────────────────────────────────
echo [2/4] Checking frontend dependencies...
if not exist "%FRONTEND_DIR%\node_modules" (
    echo  Installing frontend dependencies (first run only)...
    cd /d "%FRONTEND_DIR%"
    call npm install --legacy-peer-deps
    if %ERRORLEVEL% neq 0 (
        echo  ERROR: npm install failed.
        pause
        exit /b 1
    )
)

:: ── Start backend ───────────────────────────────────────────────────────────────
echo [3/4] Starting backend on port %BACKEND_PORT%...
cd /d "%BACKEND_DIR%"
start "A2 Backend" cmd /k "title A2 Backend (port %BACKEND_PORT%) && python -m uvicorn server:app --host 0.0.0.0 --port %BACKEND_PORT%"

:: Wait for backend to be ready
echo  Waiting for backend to start...
:wait_backend
timeout /t 2 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:%BACKEND_PORT%/api/health >nul 2>nul
if %ERRORLEVEL% neq 0 goto wait_backend

echo  Backend is live at http://localhost:%BACKEND_PORT%

:: ── Start frontend ──────────────────────────────────────────────────────────────
echo [4/4] Starting frontend on port %FRONTEND_PORT%...
cd /d "%FRONTEND_DIR%"
start "A2 Frontend" cmd /k "title A2 Frontend (port %FRONTEND_PORT%) && set BROWSER=none&& npm start"

:: Wait a moment then open browser
timeout /t 5 /nobreak >nul
start http://localhost:%FRONTEND_PORT%

echo.
echo  ============================================
echo   Platform is running!
echo.
echo   Frontend:  http://localhost:%FRONTEND_PORT%
echo   Backend:   http://localhost:%BACKEND_PORT%
echo   API Docs:  http://localhost:%BACKEND_PORT%/docs
echo.
echo   To stop: close the Backend and Frontend
echo   terminal windows, or press Ctrl+C in each.
echo  ============================================
echo.
pause
