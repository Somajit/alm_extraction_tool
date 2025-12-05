@echo off
REM Deploy entire ALM stack with MongoDB choice
REM Usage: deploy-all-with-choice.bat

set WORKSPACE_ROOT=%~dp0..

echo.
echo =============================================
echo ALM Stack - Full Deployment
echo =============================================
echo.
echo Choose MongoDB option:
echo   1. Local MongoDB (Docker container)
echo   2. MongoDB Atlas (Cloud)
echo.
set /p MONGO_CHOICE="Enter choice (1 or 2): "

if "%MONGO_CHOICE%"=="1" goto LOCAL_MONGO
if "%MONGO_CHOICE%"=="2" goto ATLAS_MONGO
goto INVALID_CHOICE

:LOCAL_MONGO
echo.
echo Selected: Local MongoDB
call "%WORKSPACE_ROOT%\scripts\switch-to-local-mongo.bat" nopause

echo.
echo [STEP 1/3] Setting up Local MongoDB...
echo.
call "%WORKSPACE_ROOT%\scripts\setup-and-test-mongo.bat"
if errorlevel 1 (
    echo [ERROR] MongoDB setup failed
    exit /b 1
)
goto DEPLOY_SERVICES

:ATLAS_MONGO
echo.
echo Selected: MongoDB Atlas
call "%WORKSPACE_ROOT%\scripts\switch-to-atlas-mongo.bat" nopause
echo.
echo [INFO] Skipping local MongoDB setup (using Atlas)
goto DEPLOY_SERVICES

:INVALID_CHOICE
echo.
echo [ERROR] Invalid choice. Please enter 1 or 2.
pause
exit /b 1

:DEPLOY_SERVICES

echo.
echo [STEP 2/3] Deploying Backend...
echo.
call "%WORKSPACE_ROOT%\scripts\deploy-backend.bat"
if errorlevel 1 (
    echo [ERROR] Backend deployment failed
    exit /b 1
)
echo.

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
echo MongoDB: %MONGO_CHOICE% (1=Local, 2=Atlas)
echo.
echo Services:
if "%MONGO_CHOICE%"=="1" (
    echo   - MongoDB: localhost:27017 ^(Local Docker^)
) else (
    echo   - MongoDB: Atlas Cloud
)
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
echo   - View backend logs: docker logs backend
echo   - View frontend logs: docker logs frontend
if "%MONGO_CHOICE%"=="1" (
    echo   - View MongoDB logs: docker logs mongo
    echo   - Stop all: docker compose -p releasecraft down
) else (
    echo   - Stop all: docker compose -p releasecraft stop backend frontend
)
echo   - Switch to Atlas: scripts\switch-to-atlas-mongo.bat
echo   - Switch to Local: scripts\switch-to-local-mongo.bat
echo.
echo API Documentation: http://localhost:8000/docs
echo.
pause
