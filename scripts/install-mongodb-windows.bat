@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MongoDB Installation Script for Windows
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires administrator privileges.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Get workspace directory
set WORKSPACE_DIR=%~dp0..
cd /d "%WORKSPACE_DIR%"
set WORKSPACE_DIR=%CD%

REM Define MongoDB version and directories in workspace
set MONGO_VERSION=7.0.4
set MONGO_DOWNLOAD_URL=https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-%MONGO_VERSION%.zip
set TEMP_ZIP=%TEMP%\mongodb.zip
set INSTALL_DIR=%WORKSPACE_DIR%\mongodb
set DATA_DIR=%WORKSPACE_DIR%\mongodb_data\db
set LOG_DIR=%WORKSPACE_DIR%\mongodb_data\log

echo Installing MongoDB Community Edition %MONGO_VERSION%...
echo.

REM Create data and log directories
echo Creating MongoDB data directories...
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo Data directory: %DATA_DIR%
echo Log directory: %LOG_DIR%
echo.

REM Download MongoDB ZIP (if not already downloaded)
if not exist "%TEMP_ZIP%" (
    echo Downloading MongoDB %MONGO_VERSION%...
    powershell -Command "& {Invoke-WebRequest -Uri '%MONGO_DOWNLOAD_URL%' -OutFile '%TEMP_ZIP%'}"
    if !errorLevel! neq 0 (
        echo ERROR: Failed to download MongoDB
        pause
        exit /b 1
    )
    echo Download complete.
) else (
    echo Using cached installer: %TEMP_ZIP%
)
echo.

REM Extract MongoDB
if exist "%INSTALL_DIR%" (
    echo Removing existing MongoDB installation...
    rmdir /s /q "%INSTALL_DIR%"
)

echo Extracting MongoDB to workspace directory...
powershell -Command "& {Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%WORKSPACE_DIR%\temp_mongo' -Force}"
if !errorLevel! neq 0 (
    echo ERROR: Failed to extract MongoDB
    pause
    exit /b 1
)

REM Move extracted files to installation directory
for /d %%i in ("%WORKSPACE_DIR%\temp_mongo\mongodb-win32-*") do (
    move "%%i" "%INSTALL_DIR%"
)
rmdir /s /q "%WORKSPACE_DIR%\temp_mongo"
echo MongoDB extracted successfully.
echo.

REM Add MongoDB to PATH (local session only)
echo Adding MongoDB to PATH for this session...
set PATH=%PATH%;%INSTALL_DIR%\bin
echo.

REM Create MongoDB configuration file
echo Creating MongoDB configuration file...
set CONFIG_FILE=%INSTALL_DIR%\mongod.cfg
(
    echo systemLog:
    echo   destination: file
    echo   path: %LOG_DIR%\mongod.log
    echo   logAppend: true
    echo storage:
    echo   dbPath: %DATA_DIR%
    echo net:
    echo   bindIp: 127.0.0.1
    echo   port: 27017
) > "%CONFIG_FILE%"
echo Configuration file created: %CONFIG_FILE%
echo.

REM Install and start MongoDB as Windows Service
echo Installing MongoDB as Windows Service...
sc create MongoDB binPath= "\"%INSTALL_DIR%\bin\mongod.exe\" --service --config=\"%CONFIG_FILE%\"" DisplayName= "MongoDB (Workspace)" start= demand
if %errorLevel% neq 0 (
    echo Warning: Failed to create MongoDB service (may already exist)
    sc delete MongoDB
    sc create MongoDB binPath= "\"%INSTALL_DIR%\bin\mongod.exe\" --service --config=\"%CONFIG_FILE%\"" DisplayName= "MongoDB (Workspace)" start= demand
) else (
    echo MongoDB service created successfully.
)

echo Starting MongoDB service...
net start MongoDB
if !errorLevel! equ 0 (
    echo MongoDB service started successfully.
) else (
    echo Starting MongoDB manually...
    start "MongoDB Server" "%INSTALL_DIR%\bin\mongod.exe" --config "%CONFIG_FILE%"
    timeout /t 3 /nobreak >nul
    echo MongoDB started manually.
)
echo.

REM Verify installation
echo Verifying MongoDB installation...
where mongod >nul 2>&1
if %errorLevel% equ 0 (
    echo MongoDB binaries are in PATH
    mongod --version
) else (
    echo Warning: MongoDB not found in PATH. You may need to restart your terminal.
)
echo.

echo ========================================
echo MongoDB Installation Complete!
echo ========================================
echo.
echo Installation directory: %INSTALL_DIR%
echo Data directory: %DATA_DIR%
echo Log directory: %LOG_DIR%
echo Config file: %CONFIG_FILE%
echo.
echo MongoDB is running as a Windows Service on port 27017
echo Connection string: mongodb://localhost:27017
echo.
echo You can manage the service using:
echo   - Start: net start MongoDB
echo   - Stop: net stop MongoDB
echo   - Status: sc query MongoDB
echo.
echo NOTE: You may need to restart your terminal for PATH changes to take effect.
echo.
pause
