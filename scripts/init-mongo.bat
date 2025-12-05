@echo off
REM Initialize MongoDB collections and indexes
REM Usage: init-mongo.bat [local|atlas] [atlas-uri]

setlocal enabledelayedexpansion

set WORKSPACE_ROOT=%~dp0..
set MONGO_TYPE=%1
set ATLAS_URI=%2

if "!MONGO_TYPE!"=="" set MONGO_TYPE=local

echo.
echo =============================================
echo MongoDB Initialization
echo =============================================
echo.

if "!MONGO_TYPE!"=="local" (
    echo Using Local MongoDB (Docker container)
    echo.
    
    REM Check if backend container is running
    docker ps | findstr "backend" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Backend container is not running
        echo Please start the backend container first with:
        echo   docker-compose up -d backend
        exit /b 1
    )
    
    echo Running MongoDB initialization script...
    docker exec backend python -m app.init_mongo
    
    if errorlevel 1 (
        echo.
        echo [ERROR] MongoDB initialization failed
        exit /b 1
    )
    
) else if "!MONGO_TYPE!"=="atlas" (
    if "!ATLAS_URI!"=="" (
        echo [ERROR] Atlas connection string is required
        echo Usage: init-mongo.bat atlas "mongodb+srv://..."
        exit /b 1
    )
    
    echo Using MongoDB Atlas (Cloud)
    echo.
    
    REM For Atlas, we need to set the MONGO_URI environment variable and run locally
    set MONGO_URI=!ATLAS_URI!
    
    echo Running MongoDB initialization script...
    cd "%WORKSPACE_ROOT%\backend"
    python app\init_mongo.py
    
    if errorlevel 1 (
        echo.
        echo [ERROR] MongoDB initialization failed
        exit /b 1
    )
    
) else (
    echo [ERROR] Invalid MongoDB type. Use 'local' or 'atlas'
    exit /b 1
)

echo.
echo =============================================
echo MongoDB Initialization Complete
echo =============================================
echo.
