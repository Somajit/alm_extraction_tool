@echo off
REM Switch backend to use Local MongoDB

setlocal enabledelayedexpansion

set BACKEND_DIR=%~dp0..\backend
set ENV_FILE=%BACKEND_DIR%\.env

echo ========================================
echo Switching to Local MongoDB
echo ========================================
echo.

REM Create .env file with local MongoDB URI
echo Creating .env file with local MongoDB configuration...
(
echo MONGO_URI=mongodb://localhost:27017/alm_db
echo CORS_ORIGINS=http://localhost:5173
) > "%ENV_FILE%"

if errorlevel 1 (
    echo [ERROR] Failed to create .env file
    pause
    exit /b 1
)

echo [SUCCESS] Backend configured for Local MongoDB
echo.
echo Configuration:
echo   URI: mongodb://localhost:27017/alm_db
echo   File: %ENV_FILE%
echo.
echo Next steps:
echo   1. Start local MongoDB: docker compose -p releasecraft up -d mongo
echo   2. Initialize data: python scripts\add_sample_data.py
echo   3. Restart backend: docker restart backend (or uvicorn app.main:app --reload)
echo.

REM Don't pause if called from another script
if "%1"=="" pause
exit /b 0
