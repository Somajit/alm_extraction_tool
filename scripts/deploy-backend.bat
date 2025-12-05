@echo off
REM Deploy ALM Backend Docker container
REM Cleans up existing container and deploys fresh instance
REM Usage: deploy-backend.bat

setlocal enabledelayedexpansion

set CONTAINER_NAME=backend
set IMAGE_NAME=releasecraft-backend
set WORKSPACE_ROOT=%~dp0..

echo.
echo ============================================
echo ALM Backend - Build and Deploy
echo ============================================
echo.

REM Step 1: Check and remove existing container
echo [STEP 1/4] Checking for existing backend container...
docker ps -a --filter "name=%CONTAINER_NAME%" --quiet >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Found existing container: %CONTAINER_NAME%
    echo [INFO] Stopping container...
    docker stop %CONTAINER_NAME% >nul 2>&1
    echo [INFO] Removing container...
    docker rm %CONTAINER_NAME% >nul 2>&1
    echo [SUCCESS] Old container cleaned up
) else (
    echo [INFO] No existing container found
)
echo.

REM Step 2: Check and remove existing image
echo [STEP 2/4] Checking for existing backend image...
docker images --filter "reference=%IMAGE_NAME%:latest" --quiet >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Found existing image: %IMAGE_NAME%:latest
    echo [INFO] Removing image...
    docker rmi %IMAGE_NAME%:latest >nul 2>&1
    echo [SUCCESS] Old image removed
) else (
    echo [INFO] No existing image found
)
echo.

REM Step 3: Build Docker image
echo [STEP 3/4] Building backend Docker image...
cd /d "%WORKSPACE_ROOT%\backend"
docker build -t %IMAGE_NAME%:latest .
if errorlevel 1 (
    echo [ERROR] Failed to build Docker image
    exit /b 1
)
echo [SUCCESS] Docker image built successfully
echo.

REM Step 4: Start container
echo [STEP 4/4] Starting backend container...
docker run -d ^
    --name %CONTAINER_NAME% ^
    -p 8000:8000 ^
    -e MONGO_URI=mongodb://mongo:27017/alm_db ^
    -e CORS_ORIGINS=http://localhost:5173 ^
    --link mongo:mongo ^
    %IMAGE_NAME%:latest

if errorlevel 1 (
    echo [ERROR] Failed to start backend container
    exit /b 1
)

echo [SUCCESS] Backend container started successfully
timeout /t 3 /nobreak

echo.
echo ============================================
echo Backend Ready!
echo ============================================
echo.
echo Container: %CONTAINER_NAME%
echo Image: %IMAGE_NAME%:latest
echo Port: 8000
echo.
echo API Documentation: http://localhost:8000/docs
echo Health Check: curl http://localhost:8000/domains
echo.
echo To stop backend:
echo   docker stop %CONTAINER_NAME%
echo.
echo To view logs:
echo   docker logs %CONTAINER_NAME%
echo.
echo To rebuild:
echo   deploy-backend.bat
echo.
