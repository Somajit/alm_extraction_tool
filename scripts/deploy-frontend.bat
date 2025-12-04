@echo off
REM Deploy ALM Frontend Docker container
REM Cleans up existing container and deploys fresh instance
REM Usage: deploy-frontend.bat

setlocal enabledelayedexpansion

set CONTAINER_NAME=alm_frontend
set IMAGE_NAME=alm_frontend
set WORKSPACE_ROOT=%~dp0..

echo.
echo ============================================
echo ALM Frontend - Build and Deploy
echo ============================================
echo.

REM Step 1: Check and remove existing container
echo [STEP 1/4] Checking for existing frontend container...
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
echo [STEP 2/4] Checking for existing frontend image...
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
echo [STEP 3/4] Building frontend Docker image...
cd /d "%WORKSPACE_ROOT%\frontend"
docker build -t %IMAGE_NAME%:latest .
if errorlevel 1 (
    echo [ERROR] Failed to build Docker image
    exit /b 1
)
echo [SUCCESS] Docker image built successfully
echo.

REM Step 4: Start container
echo [STEP 4/4] Starting frontend container...
docker run -d ^
    --name %CONTAINER_NAME% ^
    -p 5173:80 ^
    %IMAGE_NAME%:latest

if errorlevel 1 (
    echo [ERROR] Failed to start frontend container
    exit /b 1
)

echo [SUCCESS] Frontend container started successfully
timeout /t 3 /nobreak

echo.
echo ============================================
echo Frontend Ready!
echo ============================================
echo.
echo Container: %CONTAINER_NAME%
echo Image: %IMAGE_NAME%:latest
echo Port: 5173
echo.
echo Open in browser: http://localhost:5173
echo.
echo To stop frontend:
echo   docker stop %CONTAINER_NAME%
echo.
echo To view logs:
echo   docker logs %CONTAINER_NAME%
echo.
echo To rebuild:
echo   deploy-frontend.bat
echo.
