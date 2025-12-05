@echo off
REM Setup Mock ALM Service - Copy Required Files
echo ===================================
echo Mock ALM Setup - Copying Files
echo ===================================
echo.

cd /d "%~dp0.."

echo Copying mock_alm.py to mock_alm\main.py...
copy "backend\app\mock_alm.py" "mock_alm\main.py" /Y > nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] main.py copied successfully
) else (
    echo [ERROR] Failed to copy main.py
)

echo Copying alm_format_utils.py to mock_alm...
copy "backend\app\alm_format_utils.py" "mock_alm\alm_format_utils.py" /Y > nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] alm_format_utils.py copied successfully
) else (
    echo [ERROR] Failed to copy alm_format_utils.py
)

echo.
echo ===================================
echo Setup Complete!
echo ===================================
echo.
echo Files copied to mock_alm directory:
dir /b mock_alm\*.py
echo.
echo Next steps:
echo   - Run: scripts\deploy-mock-alm.bat (Docker)
echo   - OR: scripts\start-mock-alm-standalone.bat (Python)
echo.

pause
