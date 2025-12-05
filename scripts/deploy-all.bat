@echo off
REM Deploy entire ALM stack with MongoDB stats check and optional cleanup
REM Usage: deploy-all.bat

setlocal enabledelayedexpansion

set WORKSPACE_ROOT=%~dp0..

echo.
echo =============================================
echo ReleaseCraft - Full Deployment
echo =============================================
echo.

REM Ask for MongoDB type
echo Choose MongoDB deployment type:
echo   1. Local MongoDB (Docker container)
echo   2. MongoDB Atlas (Cloud)
echo.
set /p MONGO_CHOICE="Enter choice (1 or 2): "

if "!MONGO_CHOICE!"=="1" (
    set USE_LOCAL_MONGO=true
    set MONGO_TYPE=local
    set DISPLAY_MONGO_TYPE=Local MongoDB
    echo.
    echo Selected: Local MongoDB ^(Docker container^)
) else if "!MONGO_CHOICE!"=="2" (
    set USE_LOCAL_MONGO=false
    set MONGO_TYPE=atlas
    set DISPLAY_MONGO_TYPE=MongoDB Atlas
    echo.
    echo Selected: MongoDB Atlas ^(Cloud^)
    echo.
    set /p ATLAS_URI="Enter your MongoDB Atlas connection string: "
    if "!ATLAS_URI!"=="" (
        echo [ERROR] Atlas connection string is required
        exit /b 1
    )
) else (
    echo [ERROR] Invalid choice. Please enter 1 or 2.
    exit /b 1
)

REM Create .env.local with MongoDB configuration
echo.
echo Configuring MongoDB connection...
if "!USE_LOCAL_MONGO!"=="true" (
    (
        echo MONGO_URI=mongodb://localhost:27017/releasecraftdb
        echo CORS_ORIGINS=http://localhost:5173
    ) > "%WORKSPACE_ROOT%\backend\.env.local"
    echo [INFO] Configured for Local MongoDB
) else (
    (
        echo MONGO_URI=!ATLAS_URI!
        echo CORS_ORIGINS=http://localhost:5173
    ) > "%WORKSPACE_ROOT%\backend\.env.local"
    echo [INFO] Configured for MongoDB Atlas
)
echo.

REM Show current MongoDB stats
echo [STEP 1/6] Checking current MongoDB data...
if "!USE_LOCAL_MONGO!"=="true" (
    call "%WORKSPACE_ROOT%\scripts\show-detailed-mongo-stats.bat" local
    if errorlevel 1 (
        echo MongoDB not running or not accessible yet.
        echo This is normal for first-time deployment.
        set SKIP_CLEANUP=true
    )
) else (
    call "%WORKSPACE_ROOT%\scripts\show-detailed-mongo-stats.bat" atlas "!ATLAS_URI!"
    if errorlevel 1 (
        echo MongoDB Atlas not accessible.
        echo Please check your connection string.
        exit /b 1
    )
)

if not "!SKIP_CLEANUP!"=="true" (
    echo.
    set /p CLEANUP="Do you want to clean all MongoDB data? (yes/no): "
    if /I "!CLEANUP!"=="yes" (
        echo.
        echo Cleaning MongoDB data...
        if "!USE_LOCAL_MONGO!"=="true" (
            docker exec mongo mongosh releasecraftdb --quiet --eval "db.getCollectionNames().forEach(function(col) { print('Dropping: ' + col); db[col].drop(); });"
        ) else (
            mongosh "!ATLAS_URI!" --quiet --eval "db.getCollectionNames().forEach(function(col) { print('Dropping: ' + col); db[col].drop(); });"
        )
        echo.
        echo MongoDB data cleaned. New stats:
        call "%WORKSPACE_ROOT%\scripts\show-detailed-mongo-stats.bat" !MONGO_TYPE! "!ATLAS_URI!"
        set INIT_MONGO=true
    )
)
echo.

REM Step 2: Stop and remove all containers
echo [STEP 2/6] Stopping and removing all containers...
echo.
cd "%WORKSPACE_ROOT%"
docker-compose down
echo.

REM Step 3: Remove all images
echo [STEP 3/6] Removing all ReleaseCraft images...
echo.
for /f "tokens=*" %%i in ('docker images --filter^=reference^="releasecraft-*" -q') do (
    docker rmi %%i -f
)
echo Images removed.
echo.

REM Step 4: Setup MongoDB
echo [STEP 4/6] Setting up MongoDB...
echo.
if "!USE_LOCAL_MONGO!"=="true" (
    REM Clean up existing container
    echo Cleaning up existing MongoDB container...
    docker stop mongo >nul 2>&1
    docker rm mongo >nul 2>&1
    
    REM Start new MongoDB container via docker-compose
    echo Starting MongoDB container...
    cd "%WORKSPACE_ROOT%"
    docker-compose up -d mongo
    if errorlevel 1 (
        echo [ERROR] MongoDB setup failed
        exit /b 1
    )
    echo [SUCCESS] MongoDB container started
    echo [INFO] Waiting for MongoDB to initialize... ^(10 seconds^)
    timeout /t 10 /nobreak >nul
) else (
    echo Skipping local MongoDB setup - using Atlas
)
echo.

REM Step 5: Deploy Mock ALM
echo [STEP 5/6] Deploying Mock ALM Server...
echo.
call "%WORKSPACE_ROOT%\scripts\deploy-mock-alm.bat"
if errorlevel 1 (
    echo [ERROR] Mock ALM deployment failed
    exit /b 1
)
echo.

REM Step 6: Build and start all services
echo [STEP 6/6] Building and starting all services...
echo.
cd "%WORKSPACE_ROOT%"
if "!USE_LOCAL_MONGO!"=="true" (
    docker-compose build backend frontend
    docker-compose up -d
) else (
    REM For Atlas, don't start local mongo container
    docker-compose build backend frontend
    docker-compose up -d backend frontend mock-alm
)
echo.

REM Initialize MongoDB collections if data was cleaned
if "!INIT_MONGO!"=="true" (
    echo [INFO] Initializing MongoDB collections and indexes...
    echo Waiting for backend to start...
    timeout /t 5 /nobreak >nul
    docker exec backend python -m app.init_mongo
    if errorlevel 1 (
        echo [WARNING] MongoDB initialization failed, but continuing...
    ) else (
        echo [SUCCESS] MongoDB collections and indexes created
    )
    echo.
)

echo =============================================
echo SUCCESS! ReleaseCraft Deployed
echo =============================================
echo.
echo Services:
if "!USE_LOCAL_MONGO!"=="true" (
    echo   - MongoDB: localhost:27017 ^(database: releasecraftdb^)
) else (
    echo   - MongoDB: Atlas Cloud ^(releasecraftdb^)
)
echo   - Mock ALM: http://localhost:8001
echo   - Backend: http://localhost:8000
echo   - Frontend: http://localhost:5173
echo.

REM Show final MongoDB stats
echo Final MongoDB Statistics:
call "%WORKSPACE_ROOT%\scripts\show-detailed-mongo-stats.bat" !MONGO_TYPE! "!ATLAS_URI!"
echo.

echo Next steps:
echo   1. Open http://localhost:5173 in browser
echo   2. Register a new user or initialize sample data
echo.
echo Optional - Initialize sample data:
echo   scripts\initialize-sample-data.bat
echo   (Creates admin/admin123 user with test domains and projects)
echo.
echo Useful commands:
echo   - View containers: docker ps
echo   - View logs: docker logs [container-name]
echo   - Stop all: docker-compose down
echo   - MongoDB stats: scripts\show_mongo_stats.bat
echo.
echo API Documentation: http://localhost:8000/docs
echo.
