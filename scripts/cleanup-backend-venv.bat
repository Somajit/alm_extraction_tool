@echo off
REM Clean up backend venv directory

echo ======================================
echo Cleaning up backend venv
echo ======================================
echo.

set VENV_PATH=%~dp0..\backend\venv

if exist "%VENV_PATH%" (
    echo Removing: %VENV_PATH%
    rmdir /s /q "%VENV_PATH%"
    if errorlevel 1 (
        echo [ERROR] Failed to remove venv
        pause
        exit /b 1
    )
    echo [SUCCESS] Backend venv removed
) else (
    echo [INFO] Backend venv not found, nothing to clean
)

echo.
echo ======================================
echo Cleanup Complete
echo ======================================
echo.
echo Note: Using global pyenv at %USERPROFILE%\pyenv
echo.
pause
