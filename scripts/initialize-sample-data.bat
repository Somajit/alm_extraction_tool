@echo off
REM Initialize sample data in MongoDB
REM Usage: initialize-sample-data.bat

setlocal enabledelayedexpansion

set WORKSPACE_ROOT=%~dp0..

echo.
echo ============================================
echo Initialize Sample Data
echo ============================================
echo.
echo This script will create sample data in MongoDB:
echo   - 1 user (admin/admin123)
echo   - 2 domains (DomainA, DomainB)
echo   - 3 projects (Project1, Project2, ProjectX)
echo   - Sample test plans and labs
echo   - 2 defects
echo.
set /p CONFIRM="Do you want to continue? (yes/no): "

if /I not "!CONFIRM!"=="yes" (
    echo Cancelled.
    exit /b 0
)

echo.
echo Initializing sample data...
echo.

cd /d "%WORKSPACE_ROOT%"
python scripts\test_atlas_connection.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to initialize sample data
    exit /b 1
)

echo.
echo ============================================
echo Sample Data Initialized Successfully
echo ============================================
echo.
echo You can now login with:
echo   Username: admin
echo   Password: admin123
echo.
