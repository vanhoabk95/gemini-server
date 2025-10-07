@echo off
echo Starting PythonServer...
echo Current directory: %CD%
echo.

REM Move to script directory
cd /d "%~dp0"
echo Changed to directory: %CD%

REM Check virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found at .venv\Scripts\activate.bat
    echo Please check your virtual environment setup.
    exit /b 1
)

REM Check main.py
if not exist "main.py" (
    echo ERROR: main.py not found in current directory
    echo Current directory: %CD%
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Virtual environment activated. Starting PythonServer...
echo Running: python main.py --host 0.0.0.0 --port 80 --max-connections 300

python main.py --host 0.0.0.0 --port 80 --max-connections 300
