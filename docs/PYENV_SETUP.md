# Python Virtual Environment Setup

## Global Python Environment (Recommended)

A global Python virtual environment `pyenv` has been configured in your user home directory.

### Setup (One-time)

Run this script to create and setup the environment:

```cmd
scripts\setup-pyenv.bat
```

This will:
1. Create virtual environment at `%USERPROFILE%\pyenv`
2. Install all required Python packages
3. Upgrade pip, setuptools, and wheel

### Location

- **Windows:** `C:\Users\<YourUsername>\pyenv`
- **Python:** `%USERPROFILE%\pyenv\Scripts\python.exe`
- **Activate:** `%USERPROFILE%\pyenv\Scripts\activate.bat`

### VS Code Integration

VS Code is already configured to:
- Use `%USERPROFILE%\pyenv` as the Python interpreter
- Auto-activate the environment when opening a terminal
- Set PYTHONPATH to the backend directory

### Manual Activation

If needed, activate manually:

```cmd
%USERPROFILE%\pyenv\Scripts\activate.bat
```

### Installed Packages

- fastapi
- uvicorn
- motor
- pymongo
- python-dotenv
- python-multipart
- dnspython
- passlib

### Benefits

- ✅ Single virtual environment for all Python projects
- ✅ Shared across workspaces
- ✅ Persists after closing VS Code
- ✅ No need to recreate per project
