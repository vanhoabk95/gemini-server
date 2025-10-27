@echo off
echo Installing Proxy Server + Dashboard Windows Services...
echo.

REM Move to current directory and set absolute path
cd /d "%~dp0"
set "APP_DIR=%CD%"
echo Current directory: %APP_DIR%

REM Create logs directory if not exist
if not exist logs mkdir logs

REM Uninstall existing services if any (to ensure clean install)
echo Removing existing services if any...
.\nssm-2.24\win64\nssm.exe stop ProxyDashboard 2>nul
.\nssm-2.24\win64\nssm.exe stop ProxyServer 2>nul
.\nssm-2.24\win64\nssm.exe remove ProxyDashboard confirm 2>nul
.\nssm-2.24\win64\nssm.exe remove ProxyServer confirm 2>nul
REM Also remove old service name
.\nssm-2.24\win64\nssm.exe stop PythonServer 2>nul
.\nssm-2.24\win64\nssm.exe remove PythonServer confirm 2>nul

REM Wait for a moment
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo Installing Service 1: ProxyServer
echo ============================================================

REM Install ProxyServer service
.\nssm-2.24\win64\nssm.exe install ProxyServer "%APP_DIR%\start_proxy.bat"
.\nssm-2.24\win64\nssm.exe set ProxyServer AppDirectory "%APP_DIR%"
.\nssm-2.24\win64\nssm.exe set ProxyServer AppStdout "%APP_DIR%\logs\proxy_service_output.log"
.\nssm-2.24\win64\nssm.exe set ProxyServer AppStderr "%APP_DIR%\logs\proxy_service_error.log"
.\nssm-2.24\win64\nssm.exe set ProxyServer Description "Proxy Server - HTTP/HTTPS Proxy with Gemini API"
.\nssm-2.24\win64\nssm.exe set ProxyServer DisplayName "Proxy Server"
.\nssm-2.24\win64\nssm.exe set ProxyServer Start SERVICE_AUTO_START
.\nssm-2.24\win64\nssm.exe set ProxyServer AppExit Default Restart

echo ProxyServer service configured!

echo.
echo ============================================================
echo Installing Service 2: ProxyDashboard
echo ============================================================

REM Install ProxyDashboard service
.\nssm-2.24\win64\nssm.exe install ProxyDashboard "%APP_DIR%\start_dashboard.bat"
.\nssm-2.24\win64\nssm.exe set ProxyDashboard AppDirectory "%APP_DIR%"
.\nssm-2.24\win64\nssm.exe set ProxyDashboard AppStdout "%APP_DIR%\logs\dashboard_service_output.log"
.\nssm-2.24\win64\nssm.exe set ProxyDashboard AppStderr "%APP_DIR%\logs\dashboard_service_error.log"
.\nssm-2.24\win64\nssm.exe set ProxyDashboard Description "Proxy Dashboard - Streamlit Web UI"
.\nssm-2.24\win64\nssm.exe set ProxyDashboard DisplayName "Proxy Dashboard"
.\nssm-2.24\win64\nssm.exe set ProxyDashboard Start SERVICE_AUTO_START
.\nssm-2.24\win64\nssm.exe set ProxyDashboard DependOnService ProxyServer
.\nssm-2.24\win64\nssm.exe set ProxyDashboard AppExit Default Restart

echo ProxyDashboard service configured!

echo.
echo ============================================================
echo Starting services...
echo ============================================================

.\nssm-2.24\win64\nssm.exe start ProxyServer
echo Waiting for ProxyServer to start...
timeout /t 3 /nobreak >nul

.\nssm-2.24\win64\nssm.exe start ProxyDashboard
echo Waiting for ProxyDashboard to start...
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo Service Status:
echo ============================================================
.\nssm-2.24\win64\nssm.exe status ProxyServer
.\nssm-2.24\win64\nssm.exe status ProxyDashboard

echo.
echo ============================================================
echo Installation completed!
echo ============================================================
echo Working directory: %APP_DIR%
echo.
echo Services installed:
echo   1. ProxyServer (Proxy on configured port)
echo   2. ProxyDashboard (Dashboard on port 8501)
echo.
echo Logs:
echo   Proxy: %APP_DIR%\logs\proxy_service_output.log
echo   Dashboard: %APP_DIR%\logs\dashboard_service_output.log
echo.
echo Access dashboard at: http://localhost:8501
echo.
pause
