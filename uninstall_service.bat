@echo off
echo Uninstalling Proxy Server + Dashboard Windows Services...
echo.

REM Move to current directory
cd /d "%~dp0"

REM Stop services if running (reverse order)
echo Stopping services...
.\nssm-2.24\win64\nssm.exe stop ProxyDashboard 2>nul
.\nssm-2.24\win64\nssm.exe stop ProxyServer 2>nul
REM Also stop old service name if exists
.\nssm-2.24\win64\nssm.exe stop PythonServer 2>nul

REM Wait for a moment to ensure services are stopped
timeout /t 3 /nobreak >nul

REM Remove services
echo Removing services...
.\nssm-2.24\win64\nssm.exe remove ProxyDashboard confirm 2>nul
.\nssm-2.24\win64\nssm.exe remove ProxyServer confirm 2>nul
REM Also remove old service name if exists
.\nssm-2.24\win64\nssm.exe remove PythonServer confirm 2>nul

echo.
echo ============================================================
echo Services removed successfully!
echo ============================================================
echo.
echo Verifying service removal...
echo.
echo ProxyServer:
sc query ProxyServer 2>nul
if errorlevel 1 echo   [Not found - removed successfully]
echo.
echo ProxyDashboard:
sc query ProxyDashboard 2>nul
if errorlevel 1 echo   [Not found - removed successfully]
echo.
pause
