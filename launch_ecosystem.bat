@echo off
setlocal enabledelayedexpansion

:: ============================================================
::   BILLMASTER PRO - UNIFIED LAUNCHER
::   Targets: Python (Flask) + SQLite (Serverless)
:: ============================================================

set "APP_FILE=app.py"
set "PORT=5000"
set "DB_FILE=billmaster.db"

title BillMaster Pro Launcher - Active
color 0e
cls

echo.
echo  ############################################################
echo  #                                                          #
echo  #         BILLMASTER PRO STARTUP SYSTEM                    #
echo  #         [ Python / Flask / SQLite ]                      #
echo  #                                                          #
echo  ############################################################
echo.

:: 1. CHECK PYTHON
echo [1/4] Verifying Python Environment...
where python >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not detected in your PATH.
    pause
    exit /b 1
)
echo   ^> Python: Detected

:: 2. VERIFY DATABASE
echo.
echo [2/4] Checking Data Integrity...
if not exist "%DB_FILE%" (
    echo [WARNING] %DB_FILE% not found. 
    echo Flask will attempt to initialize a new database on startup.
) else (
    echo   ^> SQLite Database: %DB_FILE% (Verified)
)

:: 3. VERIFY DEPENDENCIES (Quick check for Flask)
echo.
echo [3/4] Checking Flask Dependencies...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Flask is not installed in the current environment.
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)
echo   ^> Flask Core: OK

:: 4. LAUNCH APPLICATION
echo.
echo [4/4] Starting Web Server...
echo   ^> Initializing Flask at http://127.0.0.1:%PORT%
echo.

:: Launch the app in a new minimized window
start "BillMaster Backend" /min cmd /c "python %APP_FILE%"

:: Wait for server to bind to port
echo   ^> Waiting for server to respond...
set "READY=0"
for /l %%i in (1,1,10) do (
    timeout /t 1 >nul
    netstat -ano | findstr :%PORT% >nul
    if !errorlevel! equ 0 (
        set "READY=1"
        goto :app_up
    )
)

:app_up
if "!READY!"=="0" (
    color 0C
    echo [ERROR] Server failed to start on port %PORT%. 
    echo Check if another application is using this port.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   SUCCESS: BILLMASTER PRO IS LIVE 🚀
echo  ============================================================
echo   Interface: http://localhost:%PORT%
echo   Database : SQLite Active
echo  ============================================================
echo.
echo  Opening Dashboard...
start "" "http://localhost:%PORT%"
timeout /t 3 >nul
exit
