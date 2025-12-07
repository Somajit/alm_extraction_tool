@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo ========================================
echo Local Development Environment Manager
echo ========================================
echo.

REM Step 1: Choose MongoDB connection
echo Step 1: Choose MongoDB Connection
echo --------------------------------
echo.
echo Which MongoDB do you want to connect to?
echo.
echo 1. Local MongoDB (workspace installation - localhost:27017)
echo 2. Docker MongoDB (Docker container - localhost:27017)
echo 3. MongoDB Atlas (cloud hosted)
echo 4. Custom MongoDB connection string
echo.
set /p MONGO_CHOICE="Enter your choice (1-4): "

set MONGO_URI=
set START_MONGO_LOCAL=0
if "%MONGO_CHOICE%"=="1" (
    set MONGO_URI=mongodb://localhost:27017/releasecraftdb
    set START_MONGO_LOCAL=1
    echo Selected: Local MongoDB (workspace/mongodb^)
    goto mongo_selected
)
if "%MONGO_CHOICE%"=="2" (
    set MONGO_URI=mongodb://localhost:27017/releasecraftdb
    echo Selected: Docker MongoDB (localhost:27017^)
    echo Note: Make sure Docker MongoDB container is running
    goto mongo_selected
)
if "%MONGO_CHOICE%"=="3" (
    set /p MONGO_URI="Enter MongoDB Atlas connection string: "
    echo Selected: MongoDB Atlas - !MONGO_URI!
    goto mongo_selected
)
if "%MONGO_CHOICE%"=="4" (
    set /p MONGO_URI="Enter custom MongoDB connection string: "
    echo Selected: Custom MongoDB - !MONGO_URI!
    goto mongo_selected
)
echo Invalid choice. Defaulting to Local MongoDB.
set MONGO_URI=mongodb://localhost:27017/releasecraftdb
set START_MONGO_LOCAL=1

:mongo_selected
echo.

REM Step 2: MongoDB Status and Auto-start
echo Step 2: MongoDB Status
echo ----------------------
echo.
echo Checking if MongoDB is running
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 27017); $tcp.Close(); Write-Host 'Connected to MongoDB successfully on localhost:27017'; Write-Host 'Database: releasecraftdb'; exit 0 } catch { Write-Host 'MongoDB is not running'; exit 1 }"
set MONGO_STATUS=%errorLevel%

if %MONGO_STATUS% equ 0 (
    echo MongoDB connection verified successfully!
    goto mongo_connected
)

echo MongoDB is not responding
if !START_MONGO_LOCAL! equ 1 (
        echo.
        echo MongoDB is not running. Starting local MongoDB
        
        REM Check if MongoDB is installed in workspace
        if exist "mongodb\bin\mongod.exe" (
            echo Starting MongoDB from workspace/mongodb
            
            REM Ensure directories exist
            if not exist "logs" mkdir logs
            if not exist "mongodb_data" mkdir mongodb_data
            
            REM Start MongoDB using PowerShell for better process handling
            powershell -Command "Start-Process -FilePath 'mongodb\bin\mongod.exe' -ArgumentList '--dbpath mongodb_data --bind_ip 127.0.0.1 --port 27017 --logpath logs\mongodb.log' -WindowStyle Minimized"
            
            echo Waiting for MongoDB to start (15 seconds)
            timeout /t 15 /nobreak > nul
            
            REM Check again if MongoDB is running
            powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 27017); $tcp.Close(); Write-Host 'MongoDB started successfully!'; exit 0 } catch { Write-Host 'Failed to start MongoDB'; exit 1 }"
            
            if !errorLevel! neq 0 (
                echo ERROR: Failed to start MongoDB
                echo Please check logs\mongodb.log for details
                echo.
                echo Common issues:
                echo - Port 27017 already in use
                echo - Insufficient permissions
                echo - Corrupted data directory
                echo.
                echo You can check the log file at: logs\mongodb.log
                pause
                exit /b 1
            )
        ) else (
            echo ERROR: MongoDB not found in workspace/mongodb/
            echo Please install MongoDB first or choose a different option
            pause
            exit /b 1
        )
    ) else (
        echo ERROR: Cannot connect to MongoDB at !MONGO_URI!
        echo Please make sure MongoDB is running.
        echo.
        pause
        exit /b 1
    )
)

:mongo_connected
echo.

REM Step 3: Ask to clean MongoDB
echo Step 3: Clean MongoDB Database
echo -------------------------------
echo.
set /p CLEAN_CHOICE="Do you want to clean the MongoDB database? (y/n): "

if /i "%CLEAN_CHOICE%"=="y" (
    echo.
    echo WARNING: This will delete ALL data from the releasecraftdb database!
    set /p CONFIRM="Are you sure? Type YES to confirm: "
    
    if "!CONFIRM!"=="YES" (
        echo.
        echo Cleaning MongoDB database using Python
        python -c "from pymongo import MongoClient; client = MongoClient('!MONGO_URI!'); db = client.get_database(); cols = db.list_collection_names(); [db.drop_collection(col) for col in cols]; print('Database cleaned successfully.')"
        
        if !errorLevel! equ 0 (
            echo Database cleaned successfully!
        ) else (
            echo Warning: Database cleaning may have failed. Continuing anyway...
        )
    ) else (
        echo Database cleaning cancelled.
    )
) else (
    echo Skipping database cleaning.
)
echo.

REM Step 4: Update backend .env with MongoDB URI and local URLs
echo Step 4: Configure Backend
echo -------------------------
echo.
echo Updating backend/.env with MongoDB connection and local URLs

if not exist "backend\.env" (
    echo Creating backend/.env file
    (
        echo MONGO_URI=%MONGO_URI%
        echo ALM_URL=http://localhost:8001
        echo MOCK_ALM_URL=http://localhost:8001
        echo USE_MOCK_ALM=true
        echo CORS_ORIGINS=http://localhost:5173
        echo SECRET_KEY=your-secret-key-change-in-production
    ) > backend\.env
) else (
    echo Updating environment variables in backend/.env
    powershell -Command "$content = Get-Content backend\.env; $content = $content -replace '^MONGO_URI=.*', 'MONGO_URI=%MONGO_URI%'; $content = $content -replace '^ALM_URL=.*', 'ALM_URL=http://localhost:8001'; $content = $content -replace '^MOCK_ALM_URL=.*', 'MOCK_ALM_URL=http://localhost:8001'; if ($content -notmatch 'MOCK_ALM_URL=') { $content += \"`nMOCK_ALM_URL=http://localhost:8001\" }; $content | Set-Content backend\.env"
)
echo Backend configuration updated.
echo.

REM Find available ports
echo Finding available ports...
set MOCK_ALM_PORT=8001
set BACKEND_PORT=8000
set FRONTEND_PORT=5173

REM Check and find available port for Mock ALM (starting from 8001)
:find_mock_port
netstat -ano | findstr ":%MOCK_ALM_PORT%" >nul
if %errorLevel% equ 0 (
    set /a MOCK_ALM_PORT+=1
    goto find_mock_port
)

REM Check and find available port for Backend (starting from 8000)
:find_backend_port
netstat -ano | findstr ":%BACKEND_PORT%" >nul
if %errorLevel% equ 0 (
    set /a BACKEND_PORT+=1
    goto find_backend_port
)

REM Check and find available port for Frontend (starting from 5173)
:find_frontend_port
netstat -ano | findstr ":%FRONTEND_PORT%" >nul
if %errorLevel% equ 0 (
    set /a FRONTEND_PORT+=1
    goto find_frontend_port
)

echo Ports assigned: Mock ALM=%MOCK_ALM_PORT%, Backend=%BACKEND_PORT%, Frontend=%FRONTEND_PORT%
echo.

REM Update backend .env with actual ports
powershell -Command "$content = Get-Content backend\.env; $content = $content -replace '^ALM_URL=.*', 'ALM_URL=http://localhost:%MOCK_ALM_PORT%'; $content = $content -replace '^MOCK_ALM_URL=.*', 'MOCK_ALM_URL=http://localhost:%MOCK_ALM_PORT%'; $content = $content -replace '^CORS_ORIGINS=.*', 'CORS_ORIGINS=http://localhost:%FRONTEND_PORT%'; $content | Set-Content backend\.env"

REM Step 5: Start Mock ALM Server
echo Step 5: Start Mock ALM Server
echo ------------------------------
echo.
echo Starting Mock ALM server on http://localhost:%MOCK_ALM_PORT%
start "Mock ALM Server" cmd /k "cd mock_alm && %USERPROFILE%\pyenv\Scripts\python.exe main.py --port %MOCK_ALM_PORT%"
timeout /t 3 /nobreak >nul
echo Mock ALM server started.
echo.

REM Step 6: Start Backend Server
echo Step 6: Start Backend Server
echo -----------------------------
echo.
echo Starting Backend server on http://localhost:%BACKEND_PORT%
start "Backend Server" cmd /k "cd backend && %USERPROFILE%\pyenv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"
timeout /t 5 /nobreak >nul
echo Backend server started.
echo.

REM Step 7: Start Frontend Server
echo Step 7: Start Frontend Server
echo ------------------------------
echo.
echo Starting Frontend development server on http://localhost:%FRONTEND_PORT%
start "Frontend Server" cmd /k "cd frontend && set PORT=%FRONTEND_PORT% && npm run dev"
timeout /t 3 /nobreak >nul
echo Frontend server started.
echo.

REM Write startup info to startup.log
(
echo ======================================
echo ReleaseCraft - Startup Information
echo ======================================
echo Date: %date% %time%
echo.
echo Services Running:
echo - Mock ALM:  http://localhost:%MOCK_ALM_PORT%
echo - Backend:   http://localhost:%BACKEND_PORT%
echo - Frontend:  http://localhost:%FRONTEND_PORT%
echo - MongoDB:   %MONGO_URI%
echo.
echo API Documentation: http://localhost:%BACKEND_PORT%/docs
echo.
echo Logs:
echo - Backend and services output in separate command windows
echo.
echo To stop services:
echo   1. Close each command window (Mock ALM, Backend, Frontend^)
echo   2. Or press Ctrl+C in each window
echo ======================================
) > logs\startup.log

echo ========================================
echo All Services Started Successfully!
echo ========================================
echo.
echo Services running:
echo   - Mock ALM:  http://localhost:%MOCK_ALM_PORT%
echo   - Backend:   http://localhost:%BACKEND_PORT%
echo   - Frontend:  http://localhost:%FRONTEND_PORT%
echo   - MongoDB:   %MONGO_URI%
echo.
echo Startup info saved to logs\startup.log
echo API Documentation: http://localhost:%BACKEND_PORT%/docs
echo.
echo Press any key to view the application in your browser
pause >nul

start http://localhost:%FRONTEND_PORT%

echo.
echo Application opened in browser.
echo.
echo To stop all services:
echo   1. Close each command window (Mock ALM, Backend, Frontend)
echo   2. Or press Ctrl+C in each window
echo.
echo This window can be closed safely.
echo.
pause
