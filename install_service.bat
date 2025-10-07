@echo off
echo Installing PythonServer Windows Service...
echo.

REM Move to current directory and set absolute path
cd /d "%~dp0"
set "APP_DIR=%CD%"
echo Current directory: %APP_DIR%

REM Create logs directory if not exist
if not exist logs mkdir logs

REM Uninstall service if any (to ensure clean install)
echo Removing existing service if any...
.\nssm-2.24\win64\nssm.exe stop PythonServer 2>nul
.\nssm-2.24\win64\nssm.exe remove PythonServer confirm 2>nul

REM Wait for a moment
timeout /t 2 /nobreak >nul

echo.
echo Installing new service...

REM Install service with absolute path
.\nssm-2.24\win64\nssm.exe install PythonServer "%APP_DIR%\start_app.bat"

REM Set working directory with absolute path  
.\nssm-2.24\win64\nssm.exe set PythonServer AppDirectory "%APP_DIR%"

REM Set log files with absolute path
.\nssm-2.24\win64\nssm.exe set PythonServer AppStdout "%APP_DIR%\logs\service_output.log"
.\nssm-2.24\win64\nssm.exe set PythonServer AppStderr "%APP_DIR%\logs\service_error.log"

REM Set description service
.\nssm-2.24\win64\nssm.exe set PythonServer Description "PythonServer - Proxy Server"
.\nssm-2.24\win64\nssm.exe set PythonServer DisplayName "PythonServer"

REM Set startup type is automatic
.\nssm-2.24\win64\nssm.exe set PythonServer Start SERVICE_AUTO_START

REM Set exit actions to restart on failure
.\nssm-2.24\win64\nssm.exe set PythonServer AppExit Default Restart

echo Service configuration completed!
echo.
echo Starting service now...
.\nssm-2.24\win64\nssm.exe start PythonServer
echo.
echo Checking service status...
.\nssm-2.24\win64\nssm.exe status PythonServer
echo.
echo Working directory: %APP_DIR%
echo Log files: %APP_DIR%\logs\
echo.
pause
