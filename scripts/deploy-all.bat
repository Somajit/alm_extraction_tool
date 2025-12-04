@echo off
REM Deploy entire ALM stack: MongoDB, Backend, Frontend
REM Usage: deploy-all.bat

setlocal enabledelayedexpansion

set WORKSPACE_ROOT=%~dp0..

echo.
echo =============================================
echo ALM Stack - Full Deployment
echo =============================================
echo.

REM Step 1: Setup MongoDB
echo [STEP 1/3] Setting up MongoDB...
echo.
call "%WORKSPACE_ROOT%\scripts\setup-and-test-mongo.bat"
if errorlevel 1 (
    echo [ERROR] MongoDB setup failed
    exit /b 1
)
echo.

REM Step 2: Deploy Backend
echo [STEP 2/3] Deploying Backend...
echo.
call "%WORKSPACE_ROOT%\scripts\deploy-backend.bat"
if errorlevel 1 (
    echo [ERROR] Backend deployment failed
    exit /b 1
)
echo.

REM Step 3: Deploy Frontend
echo [STEP 3/3] Deploying Frontend...
echo.
call "%WORKSPACE_ROOT%\scripts\deploy-frontend.bat"
if errorlevel 1 (
    echo [ERROR] Frontend deployment failed
    exit /b 1
)
echo.

echo.
echo =============================================
echo SUCCESS! ALM Stack Deployed
echo =============================================
echo.
echo Services:
echo   - MongoDB: localhost:27017
echo   - Backend: http://localhost:8000
echo   - Frontend: http://localhost:5173
echo.
echo Next steps:
echo   1. Open http://localhost:5173 in browser
echo   2. Login with: admin / admin123
echo   3. Select domain and project to view test plans, labs, and defects
echo.
echo Useful commands:
echo   - View all containers: docker ps
echo   - View backend logs: docker logs alm_backend
echo   - View frontend logs: docker logs alm_frontend
echo   - View MongoDB logs: docker logs alm_mongo
echo   - Stop all: docker stop alm_mongo alm_backend alm_frontend
echo   - Remove all: docker rm alm_mongo alm_backend alm_frontend
echo.
echo API Documentation: http://localhost:8000/docs
echo.
