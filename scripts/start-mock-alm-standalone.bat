@echo off
REM Start Mock ALM Server (Standalone Python)
echo =====================================
echo Starting Mock ALM Server (Standalone)
echo =====================================
echo.

cd /d "%~dp0..\mock_alm"

REM Check if files exist
if not exist "main.py" (
    echo Copying mock_alm.py to main.py...
    copy "..\backend\app\mock_alm.py" "main.py" > nul
)

if not exist "alm_format_utils.py" (
    echo Copying alm_format_utils.py...
    copy "..\backend\app\alm_format_utils.py" "alm_format_utils.py" > nul
)

echo.
echo Checking Python dependencies...
pip install -r requirements.txt > nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting Mock ALM Server on port 8001...
echo Server URL: http://localhost:8001
echo Press Ctrl+C to stop
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
