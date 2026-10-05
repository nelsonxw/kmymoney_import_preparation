@echo off
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"
set "VENV_DIR=%BACKEND_DIR%venv"

echo ========================================
echo   AI Transaction Categorization App
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo [OK] Python %PYTHON_VERSION% found

REM Check Node/npm
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set "NODE_VERSION=%%i"
echo [OK] Node.js %NODE_VERSION% found

npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('npm --version') do set "NPM_VERSION=%%i"
echo [OK] npm %NPM_VERSION% found
echo.

REM Check backend virtual environment
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [WARN] Python virtual environment not found at %VENV_DIR%
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Activate virtual environment and check requirements
call "%VENV_DIR%\Scripts\activate.bat"

if not exist "%BACKEND_DIR%\requirements.txt" (
    echo [ERROR] requirements.txt not found in backend directory.
    pause
    exit /b 1
)

echo Checking backend Python packages...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Backend packages not installed. Installing from requirements.txt...
    pip install -r "%BACKEND_DIR%\requirements.txt"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install backend packages.
        pause
        exit /b 1
    )
    echo [OK] Backend packages installed
) else (
    echo [OK] Backend packages already installed
)

REM Check frontend node_modules
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [WARN] Frontend node_modules not found. Installing dependencies...
    cd /d "%FRONTEND_DIR%"
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install frontend dependencies.
        pause
        exit /b 1
    )
    echo [OK] Frontend dependencies installed
    cd /d "%PROJECT_DIR%"
) else (
    echo [OK] Frontend dependencies already installed
)

echo.
echo ========================================
echo   All dependencies verified!
echo   Starting servers...
echo ========================================
echo.

REM Start backend in background using virtual environment Python
cd /d "%BACKEND_DIR%"
if exist "%VENV_DIR%\Scripts\python.exe" (
    start "Kmymoney Backend" cmd /k ""%VENV_DIR%\Scripts\python.exe" main.py"
) else (
    start "Kmymoney Backend" cmd /k "python main.py"
)
echo [STARTED] Backend server on http://127.0.0.1:8000

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

REM Start frontend in background
cd /d "%FRONTEND_DIR%"
start "Kmymoney Frontend" cmd /k "npm run dev"
echo [STARTED] Frontend server on http://localhost:5173

echo.
echo ========================================
echo   App is running!
echo   Frontend: http://localhost:5173
echo   Backend:  http://127.0.0.1:8000
echo ========================================
echo.
echo Press any key to close this window (servers will continue running in separate windows)...
pause >nul
