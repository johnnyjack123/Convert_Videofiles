@echo off
setlocal

cd /d "%~dp0"

set VENV_DIR=venv

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create virtual environment.
        exit /b 1
    )

    call "%VENV_DIR%\Scripts\activate.bat"

    echo Installing requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install requirements.
        exit /b 1
    )
) else (
    call "%VENV_DIR%\Scripts\activate.bat"
)

python main.py %*

endlocal
