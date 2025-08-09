@echo off
title Proxy Server (Admin)

:: Check for admin rights and elevate if needed
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if %errorlevel% neq 0 (
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B
)

echo ========================================
echo    Simple Python Proxy Server
echo ========================================
echo.
echo Starting server with admin privileges...
echo Host: 0.0.0.0
echo Port: 80
echo Max Connections: 150
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

uv run python main.py

pause