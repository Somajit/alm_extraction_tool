@echo off
REM Switch backend to use MongoDB Atlas

setlocal enabledelayedexpansion

set BACKEND_DIR=%~dp0..\backend
set ENV_FILE=%BACKEND_DIR%\.env

echo ========================================
echo Switching to MongoDB Atlas
echo ========================================
echo.

REM Create .env file with Atlas MongoDB URI
echo Creating .env file with Atlas MongoDB configuration...
(
echo MONGO_URI=mongodb+srv://admin:admin123@cluster0.uilvvya.mongodb.net/alm_db?retryWrites=true^&w=majority
echo CORS_ORIGINS=http://localhost:5173
) > "%ENV_FILE%"

if errorlevel 1 (
    echo [ERROR] Failed to create .env file
    pause
    exit /b 1
)

echo [SUCCESS] Backend configured for MongoDB Atlas
echo.
echo Configuration:
echo   URI: mongodb+srv://admin:admin123@cluster0.uilvvya.mongodb.net/alm_db
echo   File: %ENV_FILE%
echo.
echo Next steps:
echo   1. Ensure Atlas cluster is running
echo   2. Initialize data (if needed): python scripts\add_sample_data.py
echo   3. Restart backend: docker restart backend (or uvicorn app.main:app --reload)
echo.
echo Note: You can stop local MongoDB if running:
echo   docker compose -p releasecraft stop mongo
echo.

REM Don't pause if called from another script
if "%1"=="" pause
exit /b 0
