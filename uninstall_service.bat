@echo off
echo Uninstalling PythonServer Windows Service...
echo.

REM Move to current directory
cd /d "%~dp0"

REM Stop service if running
echo Stopping service...
.\nssm-2.24\win64\nssm.exe stop PythonServer

REM Wait for a moment to ensure service is stopped
timeout /t 3 /nobreak >nul

REM Remove service
echo Removing service...
.\nssm-2.24\win64\nssm.exe remove PythonServer confirm

echo.
echo Service removed successfully!
echo.
echo Verifying service removal...
sc query PythonServer
echo.
pause
