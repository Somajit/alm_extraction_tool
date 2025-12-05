@echo off
REM Deploy Mock ALM Server Script
echo =====================================
echo Deploying Mock ALM Server
echo =====================================
echo.

cd /d "%~dp0.."

REM Check if files exist in mock_alm
if not exist "mock_alm\main.py" (
    echo Copying mock_alm.py to mock_alm\main.py...
    copy "backend\app\mock_alm.py" "mock_alm\main.py" > nul
)

if not exist "mock_alm\alm_format_utils.py" (
    echo Copying alm_format_utils.py to mock_alm...
    copy "backend\app\alm_format_utils.py" "mock_alm\alm_format_utils.py" > nul
)

echo.
echo Building and starting Mock ALM container...
docker-compose up -d --build mock-alm

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =====================================
    echo Mock ALM Server Deployed Successfully!
    echo =====================================
    echo.
    echo Server running at: http://localhost:8001
    echo Health check: curl http://localhost:8001/
    echo.
    echo View logs: docker logs alm_mock_server -f
    echo Stop server: docker-compose stop mock-alm
    echo.
) else (
    echo.
    echo =====================================
    echo Deployment Failed!
    echo =====================================
    echo Please check the error messages above.
)
