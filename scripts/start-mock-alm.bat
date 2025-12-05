@echo off
REM Start Mock ALM Server
REM This script starts the mock ALM REST API server on port 8001

echo ========================================
echo Starting Mock ALM Server
echo ========================================
echo.

REM Check if Python venv exists
if not exist "%USERPROFILE%\pyenv\Scripts\activate.bat" (
    echo Error: Python virtual environment not found at %USERPROFILE%\pyenv
    echo Please run setup-python-env.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call "%USERPROFILE%\pyenv\Scripts\activate.bat"

REM Change to backend directory
cd /d "%~dp0..\backend\app"

echo.
echo Mock ALM Server will start on: http://localhost:8001
echo.
echo Authentication endpoints:
echo   POST http://localhost:8001/qcbin/authentication-point/authenticate
echo   POST http://localhost:8001/qcbin/rest/site-session
echo.
echo API endpoints:
echo   GET  http://localhost:8001/qcbin/rest/domains
echo   GET  http://localhost:8001/qcbin/rest/domains/{domain}/projects
echo   GET  http://localhost:8001/qcbin/rest/domains/{domain}/projects/{project}/test-folders
echo   GET  http://localhost:8001/qcbin/rest/domains/{domain}/projects/{project}/tests
echo.
echo Press Ctrl+C to stop the server
echo.
echo ========================================

REM Start the mock ALM server
python mock_alm.py

pause
