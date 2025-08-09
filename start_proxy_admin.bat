@echo off
echo Requesting administrator privileges...

:: Check for admin rights and elevate if needed
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if %errorlevel% neq 0 (
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B
)

echo Starting Python Proxy Server with admin rights...
echo Host: 0.0.0.0
echo Port: 80
echo Max connections: 50
echo.
echo Press Ctrl+C to stop the server
echo.

uv run python main.py --host 0.0.0.0 --port 80 --max-connections 50 --log-level DEBUG

echo.
echo Server stopped
pause 