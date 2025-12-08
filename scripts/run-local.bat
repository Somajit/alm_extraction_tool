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

REM Try to read MONGO_URI from backend/.env if it exists
if exist "backend\.env" (
    REM Read the entire line and extract value after =, removing quotes if present
    for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b "MONGO_URI=" backend\.env`) do (
        set "EXISTING_MONGO_URI=%%b"
        REM Remove surrounding quotes if present
        set EXISTING_MONGO_URI=!EXISTING_MONGO_URI:"=!
    )
)

if "%MONGO_CHOICE%"=="1" (
    if defined EXISTING_MONGO_URI (
        set MONGO_URI=!EXISTING_MONGO_URI!
    ) else (
        set MONGO_URI=mongodb://localhost:27017/almdb
    )
    set START_MONGO_LOCAL=1
    echo Selected: Local MongoDB (workspace/mongodb^)
    goto mongo_selected
)
if "%MONGO_CHOICE%"=="2" (
    if defined EXISTING_MONGO_URI (
        set MONGO_URI=!EXISTING_MONGO_URI!
    ) else (
        set MONGO_URI=mongodb://localhost:27017/almdb
    )
    echo Selected: Docker MongoDB (localhost:27017^)
    echo Note: Make sure Docker MongoDB container is running
    goto mongo_selected
)
if "%MONGO_CHOICE%"=="3" (
    if defined EXISTING_MONGO_URI (
        echo Found existing MongoDB URI in .env: !EXISTING_MONGO_URI!
        set /p USE_EXISTING="Use this connection? (y/n, default=y): "
        if /i "!USE_EXISTING!"=="" set USE_EXISTING=y
        if /i "!USE_EXISTING!"=="y" (
            set MONGO_URI=!EXISTING_MONGO_URI!
        ) else (
            set /p MONGO_URI="Enter MongoDB Atlas connection string: "
        )
    ) else (
        set /p MONGO_URI="Enter MongoDB Atlas connection string: "
    )
    echo Selected: MongoDB Atlas - !MONGO_URI!
    goto mongo_selected
)
if "%MONGO_CHOICE%"=="4" (
    if defined EXISTING_MONGO_URI (
        echo Found existing MongoDB URI in .env: !EXISTING_MONGO_URI!
        set /p USE_EXISTING="Use this connection? (y/n, default=y): "
        if /i "!USE_EXISTING!"=="" set USE_EXISTING=y
        if /i "!USE_EXISTING!"=="y" (
            set MONGO_URI=!EXISTING_MONGO_URI!
        ) else (
            set /p MONGO_URI="Enter custom MongoDB connection string: "
        )
    ) else (
        set /p MONGO_URI="Enter custom MongoDB connection string: "
    )
    echo Selected: Custom MongoDB - !MONGO_URI!
    goto mongo_selected
)
echo Invalid choice. Defaulting to Local MongoDB.
if defined EXISTING_MONGO_URI (
    set MONGO_URI=!EXISTING_MONGO_URI!
) else (
    set MONGO_URI=mongodb://localhost:27017/almdb
)
set START_MONGO_LOCAL=1

:mongo_selected
echo.

REM Activate Python virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating Python virtual environment...
    call venv\Scripts\activate.bat
    echo Virtual environment activated
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating Python virtual environment...
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo No virtual environment found at venv\ or .venv\
    echo Using system Python
)
echo.

REM Detect Python executable early (needed for MongoDB tests)
set PYTHON_CMD=
if exist "%USERPROFILE%\pyenv\Scripts\python.exe" (
    set PYTHON_CMD=%USERPROFILE%\pyenv\Scripts\python.exe
    echo Using Python from: %USERPROFILE%\pyenv\Scripts\python.exe
    goto python_found
)

REM Try python3 command
python3 --version >nul 2>&1
if %errorLevel% equ 0 (
    set PYTHON_CMD=python3
    echo Using python3
    goto python_found
)

REM Try python command
python --version >nul 2>&1
if %errorLevel% equ 0 (
    set PYTHON_CMD=python
    echo Using python
    goto python_found
)

REM Try py launcher
py --version >nul 2>&1
if %errorLevel% equ 0 (
    set PYTHON_CMD=py
    echo Using py launcher
    goto python_found
)

echo WARNING: Python not found in PATH
echo MongoDB connection test will be skipped
echo Please ensure Python is installed and added to PATH
set PYTHON_CMD=python
echo.

:python_found
echo.

REM Check if pymongo is installed
echo Checking for pymongo...
%PYTHON_CMD% -c "import pymongo" >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: pymongo module not found in current environment
    echo Please install dependencies: pip install -r backend\requirements.txt
    echo Skipping MongoDB connection test...
    set SKIP_MONGO_TEST=1
) else (
    echo pymongo found
    set SKIP_MONGO_TEST=0
)
echo.

REM Step 2: MongoDB Status and Auto-start
echo Step 2: MongoDB Status
echo ----------------------
echo.

REM Only check localhost MongoDB for options 1 and 2
if %MONGO_CHOICE% equ 1 goto check_local_mongo
if %MONGO_CHOICE% equ 2 goto check_local_mongo

REM For options 3 and 4 (Atlas/Custom), test remote MongoDB connection
echo Using remote MongoDB connection
echo Connection: !MONGO_URI!
echo.

REM Extract database name from MONGO_URI
REM Handle URIs like: mongodb://user:pass@host:port/dbname?authSource=dbname
for /f "tokens=*" %%a in ("!MONGO_URI!") do set TEMP_URI=%%a
for /f "tokens=4 delims=/" %%a in ("!TEMP_URI!") do set DB_WITH_PARAMS=%%a
for /f "tokens=1 delims=?" %%a in ("!DB_WITH_PARAMS!") do set DB_NAME=%%a
if "!DB_NAME!"==" " set DB_NAME=test
echo Database: !DB_NAME!
echo.

echo Testing MongoDB connection...
if %SKIP_MONGO_TEST% equ 1 (
    echo Skipping connection test - pymongo not available
    echo Connection will be tested when starting services.
    goto mongo_connected
)

REM Create temporary Python script to test connection
(
echo import sys
echo from pymongo import MongoClient
echo uri = r"""!MONGO_URI!"""
echo try:
echo     client = MongoClient^(uri, serverSelectionTimeoutMS=5000^)
echo     client.server_info^(^)
echo     print^('Connected to MongoDB successfully'^)
echo     sys.exit^(0^)
echo except Exception as e:
echo     print^(f'Error: {e}'^)
echo     sys.exit^(1^)
) > test_mongo.py

%PYTHON_CMD% test_mongo.py
set CONN_STATUS=%errorLevel%
del test_mongo.py 2>nul

if %CONN_STATUS% equ 0 (
    echo Connection verified successfully!
    echo.
    
    REM Ask user if they want to clean the database
    echo.
    set /p CLEAN_DB="Do you want to clean the database? (y/N): "
    if /i "!CLEAN_DB!"=="y" (
        echo Cleaning database...
        (
        echo from pymongo import MongoClient
        echo uri = r"""!MONGO_URI!"""
        echo client = MongoClient^(uri^)
        echo db = client.get_database^(^)
        echo collections = db.list_collection_names^(^)
        echo for col in collections:
        echo     db[col].delete_many^({}^)
        echo     print^(f'Cleared collection: {col}'^)
        echo print^('Database cleaned successfully'^)
        ^) > clean_mongo.py
        
        %PYTHON_CMD% clean_mongo.py
        del clean_mongo.py 2>nul
        echo.
    )
    
    echo Fetching collection statistics...
    REM Create temporary Python script for statistics
    (
    echo from pymongo import MongoClient
    echo uri = r"""!MONGO_URI!"""
    echo client = MongoClient^(uri^)
    echo db = client.get_database^(^)
    echo collections = db.list_collection_names^(^)
    echo print^(''^)
    echo print^('Collections:'^)
    echo print^('-' * 50^)
    echo if collections:
    echo     for col in sorted^(collections^):
    echo         count = db[col].count_documents^({}^)
    echo         print^(f'{col}: {count} documents'^)
    echo     total = sum^([db[col].count_documents^({}^) for col in collections]^)
    echo     print^('-' * 50^)
    echo     print^(f'Total documents: {total}'^)
    echo else:
    echo     print^('No collections found'^)
    ^) > stats_mongo.py
    
    %PYTHON_CMD% stats_mongo.py
    del stats_mongo.py 2>nul
) else (
    echo Warning: Could not verify connection
    echo Please check: 1) URI is correct, 2) Network connectivity, 3) Credentials
    echo Continuing anyway... Connection will be tested when starting services.
)
goto mongo_connected

:check_local_mongo
echo Checking if MongoDB is running on localhost:27017
REM Extract database name from MONGO_URI
for /f "tokens=*" %%a in ("!MONGO_URI!") do set TEMP_URI=%%a
for /f "tokens=4 delims=/" %%a in ("!TEMP_URI!") do set DB_WITH_PARAMS=%%a
for /f "tokens=1 delims=?" %%a in ("!DB_WITH_PARAMS!") do set DB_NAME=%%a
if "!DB_NAME!"=="" set DB_NAME=almdb
echo Database: !DB_NAME!
echo.
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 27017); $tcp.Close(); Write-Host 'Connected to MongoDB successfully on localhost:27017'; exit 0 } catch { Write-Host 'MongoDB is not running'; exit 1 }"
set MONGO_STATUS=%errorLevel%

if %MONGO_STATUS% equ 0 (
    echo Connection verified successfully!
    echo.
    
    REM Ask user if they want to clean the database
    echo.
    set /p CLEAN_DB="Do you want to clean the database? (y/N): "
    if /i "!CLEAN_DB!"=="y" (
        echo Cleaning database...
        (
        echo from pymongo import MongoClient
        echo uri = r"""!MONGO_URI!"""
        echo client = MongoClient^(uri^)
        echo db = client.get_database^(^)
        echo collections = db.list_collection_names^(^)
        echo for col in collections:
        echo     db[col].delete_many^({}^)
        echo     print^(f'Cleared collection: {col}'^)
        echo print^('Database cleaned successfully'^)
        ^) > clean_mongo.py
        
        %PYTHON_CMD% clean_mongo.py
        del clean_mongo.py 2>nul
        echo.
    )
    
    echo Fetching collection statistics...
    REM Create temporary Python script for statistics
    (
    echo from pymongo import MongoClient
    echo uri = r"""!MONGO_URI!"""
    echo client = MongoClient^(uri^)
    echo db = client.get_database^(^)
    echo collections = db.list_collection_names^(^)
    echo print^(''^)
    echo print^('Collections:'^)
    echo print^('-' * 50^)
    echo if collections:
    echo     for col in sorted^(collections^):
    echo         count = db[col].count_documents^({}^)
    echo         print^(f'{col}: {count} documents'^)
    echo     total = sum^([db[col].count_documents^({}^) for col in collections]^)
    echo     print^('-' * 50^)
    echo     print^(f'Total documents: {total}'^)
    echo else:
    echo     print^('No collections found'^)
    ^) > stats_mongo.py
    
    %PYTHON_CMD% stats_mongo.py
    del stats_mongo.py 2>nul
    
    %PYTHON_CMD% stats_mongo.py
    del stats_mongo.py
    goto mongo_connected
)

echo Not responding
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
    REM Extract database name from MONGO_URI for warning
    for /f "tokens=*" %%a in ("!MONGO_URI!") do set TEMP_URI=%%a
    for /f "tokens=4 delims=/" %%a in ("!TEMP_URI!") do set DB_WITH_PARAMS=%%a
    for /f "tokens=1 delims=?" %%a in ("!DB_WITH_PARAMS!") do set DB_NAME=%%a
    if "!DB_NAME!"=="" set DB_NAME=almdb
    echo WARNING: This will delete ALL data from the !DB_NAME! database!
    set /p CONFIRM="Are you sure? Type YES to confirm: "
    
    if "!CONFIRM!"=="YES" (
        echo.
        echo Cleaning MongoDB database using Python
        python -c "from pymongo import MongoClient; client = MongoClient('''!MONGO_URI!'''); db = client.get_database(); cols = db.list_collection_names(); [db.drop_collection(col) for col in cols]; print('Database cleaned successfully.')"
        
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

REM Step 4: Configure Backend
echo Step 4: Configure Backend
echo -------------------------
echo.

REM Read USE_MOCK_ALM setting if it exists
set USE_MOCK_ALM=true
if exist "backend\.env" (
    for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b "USE_MOCK_ALM=" backend\.env`) do (
        set "USE_MOCK_ALM=%%b"
    )
)

if not exist "backend\.env" (
    echo Creating backend/.env file
    (
        echo MONGO_URI=!MONGO_URI!
        echo ALM_BASE_URL=http://localhost:8001
        echo USE_MOCK_ALM=true
        echo CORS_ORIGINS=http://localhost:5173
        echo SECRET_KEY=your-secret-key-change-in-production
    ) > backend\.env
    echo Backend configuration created.
) else (
    echo Updating MONGO_URI in backend/.env
    powershell -Command "$content = Get-Content 'backend\.env' -Raw; $content = $content -replace '(?m)^MONGO_URI=.*$', 'MONGO_URI=!MONGO_URI!'; $content | Set-Content 'backend\.env' -NoNewline"
    
    REM Only update ALM_BASE_URL if USE_MOCK_ALM is true
    if /i "!USE_MOCK_ALM!"=="true" (
        echo USE_MOCK_ALM is enabled - will update ALM_BASE_URL for Mock ALM
    ) else (
        echo USE_MOCK_ALM is disabled - keeping existing ALM_BASE_URL
    )
)
echo Backend configuration updated.
echo.

REM Python executable already detected earlier
REM Continuing with port detection...

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

REM Update backend .env with actual ports, but only update ALM_BASE_URL if USE_MOCK_ALM=true
if /i "!USE_MOCK_ALM!"=="true" (
    powershell -Command "$content = Get-Content 'backend\.env' -Raw; $content = $content -replace '(?m)^ALM_BASE_URL=.*$', 'ALM_BASE_URL=http://localhost:%MOCK_ALM_PORT%'; $content = $content -replace '(?m)^CORS_ORIGINS=.*$', 'CORS_ORIGINS=http://localhost:%FRONTEND_PORT%'; $content | Set-Content 'backend\.env' -NoNewline"
    echo Updated ALM_BASE_URL to http://localhost:%MOCK_ALM_PORT% (Mock ALM)
) else (
    powershell -Command "$content = Get-Content 'backend\.env' -Raw; $content = $content -replace '(?m)^CORS_ORIGINS=.*$', 'CORS_ORIGINS=http://localhost:%FRONTEND_PORT%'; $content | Set-Content 'backend\.env' -NoNewline"
    echo Keeping existing ALM_BASE_URL (Mock ALM disabled)
)
echo.
REM Initialize admin user in MongoDB
echo Initializing admin user...
cd backend
%PYTHON_CMD% init_admin.py
if %errorLevel% neq 0 (
    echo Warning: Failed to initialize admin user
)
cd ..
echo.

REM Step 5: Start Mock ALM Server (only if USE_MOCK_ALM=true)
if /i "!USE_MOCK_ALM!"=="true" (
    echo Step 5: Start Mock ALM Server
    echo ------------------------------
    echo.
    echo Starting Mock ALM server on http://localhost:%MOCK_ALM_PORT%
    start "Mock ALM Server" cmd /k "cd mock_alm && %PYTHON_CMD% main.py --port %MOCK_ALM_PORT%"
    timeout /t 3 /nobreak >nul
    echo Mock ALM server started.
    echo.
) else (
    echo Step 5: Mock ALM Server
    echo ------------------------
    echo Skipping Mock ALM (USE_MOCK_ALM=false)
    echo.
)

REM Step 6: Start Backend Server
echo Step 6: Start Backend Server
echo -----------------------------
echo.
echo Starting Backend server on http://localhost:%BACKEND_PORT%
start "Backend Server" cmd /k "cd backend && %PYTHON_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"
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
