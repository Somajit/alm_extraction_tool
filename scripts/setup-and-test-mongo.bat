@echo off
REM All-in-one MongoDB setup: clean, start, and test
REM Usage: setup-and-test-mongo.bat

setlocal enabledelayedexpansion

set CONTAINER_NAME=alm_mongo
set MONGO_URI=mongodb://localhost:27017/alm_db
set WORKSPACE_ROOT=%~dp0..

echo.
echo ============================================
echo MongoDB Setup - Clean, Start, and Test
echo ============================================
echo.

REM Step 1: Clean up existing container
echo [STEP 1/3] Cleaning up existing MongoDB container...
docker ps -a --filter "name=%CONTAINER_NAME%" --quiet >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Stopping existing container...
    docker stop %CONTAINER_NAME% >nul 2>&1
    echo [INFO] Removing existing container...
    docker rm %CONTAINER_NAME% >nul 2>&1
    echo [SUCCESS] Container cleaned up
) else (
    echo [INFO] No existing container found
)
echo.

REM Step 2: Start new MongoDB container
echo [STEP 2/3] Starting new MongoDB container...
docker run -d --name %CONTAINER_NAME% -p 27017:27017 -e MONGO_INITDB_DATABASE=alm_db mongo:6.0
if errorlevel 1 (
    echo [ERROR] Failed to start MongoDB container
    exit /b 1
)
echo [SUCCESS] MongoDB container started
echo [INFO] Waiting for MongoDB to initialize... (10 seconds)
timeout /t 10 /nobreak
echo.

REM Step 3: Test connection and initialize data
echo [STEP 3/3] Testing connection and initializing sample data...

REM Create .env.local file
(
    echo MONGO_URI=%MONGO_URI%
    echo CORS_ORIGINS=http://localhost:5173
) > "%WORKSPACE_ROOT%\backend\.env.local"

echo [INFO] Created .env.local
echo [INFO] Running test and initialization script...
echo.

cd /d "%WORKSPACE_ROOT%"
python scripts\test_atlas_connection.py

if errorlevel 1 (
    echo.
    echo [ERROR] Connection test failed
    echo.
    echo Troubleshooting:
    echo   1. Check MongoDB logs: docker logs %CONTAINER_NAME%
    echo   2. Verify port 27017 is available: netstat -ano | findstr :27017
    echo   3. Try restarting Docker Desktop
    exit /b 1
)

echo.
echo ============================================
echo SUCCESS! MongoDB is ready
echo ============================================
echo.
echo Next steps:
echo   1. Backend: cd backend ^&^& uvicorn app.main:app --reload
echo   2. Frontend: cd frontend ^&^& npm run dev
echo   3. Open: http://localhost:5173
echo   4. Login: admin / admin123
echo.
echo To stop MongoDB:
echo   docker stop %CONTAINER_NAME%
echo.
echo To clean up MongoDB completely:
echo   docker stop %CONTAINER_NAME% ^&^& docker rm %CONTAINER_NAME%
echo.
