@echo off
REM Setup Python virtual environment in user home directory

echo ======================================
echo Creating Python Virtual Environment
echo ======================================
echo.
echo Location: %USERPROFILE%\pyenv
echo.

REM Create virtual environment
python -m venv %USERPROFILE%\pyenv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [SUCCESS] Virtual environment created
echo.
echo Activating virtual environment...
call %USERPROFILE%\pyenv\Scripts\activate.bat

echo.
echo Installing required packages...
echo.

pip install --upgrade pip setuptools wheel
pip install fastapi uvicorn motor pymongo python-dotenv python-multipart dnspython passlib

if errorlevel 1 (
    echo [ERROR] Failed to install packages
    pause
    exit /b 1
)

echo.
echo ======================================
echo SUCCESS - Setup Complete
echo ======================================
echo.
echo Virtual environment location: %USERPROFILE%\pyenv
echo Python executable: %USERPROFILE%\pyenv\Scripts\python.exe
echo.
echo To activate manually: %USERPROFILE%\pyenv\Scripts\activate.bat
echo.
pause
