# Virtual Environment Migration

## What Changed

Migrated from project-local virtual environment to a global user-level virtual environment.

### Before
- Virtual environment: `backend/venv/`
- Manually activated per terminal session
- Project-specific

### After
- Virtual environment: `%USERPROFILE%\pyenv` (e.g., `C:\Users\Somajit\pyenv`)
- Auto-activates in VS Code terminals
- Global across all projects

## Setup Instructions

### 1. Create Global Virtual Environment

Run once:
```cmd
scripts\setup-pyenv.bat
```

This will:
- Create `%USERPROFILE%\pyenv`
- Install all Python packages (fastapi, uvicorn, motor, pymongo, etc.)
- Upgrade pip, setuptools, wheel

### 2. Clean Up Old Virtual Environment (Optional)

Remove the old backend/venv:
```cmd
scripts\cleanup-backend-venv.bat
```

### 3. Verify VS Code Integration

Open a new terminal in VS Code - you should see:
```
Activating Python virtual environment...

Virtual environment activated!
Python: C:\Users\<YourUsername>\pyenv
```

## Benefits

✅ Single virtual environment for all Python work
✅ Auto-activates in VS Code
✅ Persists across VS Code sessions
✅ No need to remember activation commands
✅ Shared packages across projects

## Files Modified

- `.vscode/settings.json` - Updated Python interpreter path
- `activate-env.bat` - Points to global pyenv
- `.gitignore` - Added backend/venv/ to ignore list
- `README.md` - Updated setup instructions

## New Files Created

- `scripts/setup-pyenv.bat` - Creates and configures global pyenv
- `scripts/cleanup-backend-venv.bat` - Removes old backend/venv
- `docs/PYENV_SETUP.md` - Documentation

## Troubleshooting

**Virtual environment not activating?**
- Close and reopen VS Code
- Run: `scripts\setup-pyenv.bat`

**Packages missing?**
- Activate manually: `%USERPROFILE%\pyenv\Scripts\activate.bat`
- Install: `pip install <package_name>`

**Want to use project-local venv again?**
- Update `.vscode/settings.json` → `python.defaultInterpreterPath`
- Change terminal profile args in settings.json
