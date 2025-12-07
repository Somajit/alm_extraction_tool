@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo ========================================
echo Starting ALM Extraction Tool Locally
echo ========================================
echo.

REM Update backend .env for local execution
echo Configuring backend for local execution...
powershell -Command "$content = Get-Content backend\.env; $content = $content -replace '^MONGO_URI=.*', 'MONGO_URI=mongodb://localhost:27017/releasecraftdb'; $content = $content -replace '^ALM_URL=.*', 'ALM_URL=http://localhost:8001'; $content = $content -replace '^MOCK_ALM_URL=.*', 'MOCK_ALM_URL=http://localhost:8001'; if ($content -notmatch 'MOCK_ALM_URL=') { $content += \"`nMOCK_ALM_URL=http://localhost:8001\" }; $content | Set-Content backend\.env"
echo.

REM Check if MongoDB is running
echo Checking MongoDB...
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 27017); $tcp.Close(); Write-Host '√ MongoDB is running on localhost:27017'; exit 0 } catch { Write-Host 'X MongoDB is not running. Please start MongoDB first.'; Write-Host '  Run: mongodb\bin\mongod.exe --config mongodb\mongod.cfg'; exit 1 }"
if %errorLevel% neq 0 (
    echo.
    pause
    exit /b 1
)
echo.

REM Start Mock ALM
echo Starting Mock ALM Server (port 8001)...
start "Mock ALM Server" cmd /k "cd mock_alm && %USERPROFILE%\pyenv\Scripts\python.exe main.py"
timeout /t 2 /nobreak >nul
echo.

REM Start Backend
echo Starting Backend Server (port 8000)...
start "Backend Server" cmd /k "cd backend && %USERPROFILE%\pyenv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
echo.

REM Start Frontend
echo Starting Frontend Server (port 5173)...
start "Frontend Server" cmd /k "cd frontend && npm run dev"
timeout /t 2 /nobreak >nul
echo.

echo ========================================
echo All Services Started!
echo ========================================
echo.
echo Services:
echo   Mock ALM:  http://localhost:8001
echo   Backend:   http://localhost:8000 (API Docs: /docs)
echo   Frontend:  http://localhost:5173
echo.
echo Opening application in 3 seconds...
timeout /t 3 /nobreak >nul

start http://localhost:5173

echo.
echo Application opened in browser.
echo Check the separate windows for each service.
echo.
pause
