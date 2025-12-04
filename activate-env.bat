@echo off
REM Activate Python virtual environment
REM This script is automatically sourced when opening terminal in VS Code

echo Activating Python virtual environment...
call %USERPROFILE%\pyenv\Scripts\activate.bat
if errorlevel 1 (
    echo [WARNING] Virtual environment not found at %USERPROFILE%\pyenv
    echo.
    echo Run: scripts\setup-pyenv.bat to create it
    echo.
) else (
    echo.
    echo Virtual environment activated!
    echo Python: %VIRTUAL_ENV%
    echo.
)

echo Available commands:
echo   - cd backend; uvicorn app.main:app --reload  (Run backend)
echo   - cd frontend; npm run dev                   (Run frontend)
echo   - cd scripts; python add_sample_data.py      (Add sample data)
echo   - scripts\deploy-all.bat                     (Deploy with Docker)
echo   - scripts\setup-pyenv.bat                    (Setup Python venv)
echo.
