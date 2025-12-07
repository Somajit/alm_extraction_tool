@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo Stopping all services...
echo.

REM Kill processes on specific ports
echo Stopping Frontend (port 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Stopping Backend (port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Stopping Mock ALM (port 8001)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM Close command windows by title
taskkill /FI "WINDOWTITLE eq Mock ALM Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Backend Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend Server*" /F >nul 2>&1

echo.
echo All services stopped.
echo.
pause
