@echo off
echo ================================================================
echo  Starting SUT Service
echo ================================================================
echo.

set INSTALL_DIR=C:\Program Files\SUTService

REM Check if service is installed
if not exist "%INSTALL_DIR%\SUTService.exe" (
    echo ERROR: SUT Service not installed!
    echo Please run install_sut_service.bat first
    pause
    exit /b 1
)

REM Check if already running
tasklist /FI "IMAGENAME eq SUTService.exe" 2>nul | find /I "SUTService.exe" >nul
if not errorlevel 1 (
    echo SUT Service is already running!
    echo.
    pause
    exit /b 0
)

REM Start via scheduled task (preserves admin privileges)
echo Starting SUT Service via scheduled task...
schtasks /run /tn "SUTService"

if errorlevel 1 (
    echo ERROR: Failed to start service via scheduled task
    echo Trying direct launch...
    start "" "%INSTALL_DIR%\SUTService.exe"
)

timeout /t 2 /nobreak >nul

REM Check if started
tasklist /FI "IMAGENAME eq SUTService.exe" 2>nul | find /I "SUTService.exe" >nul
if not errorlevel 1 (
    echo.
    echo ================================================================
    echo SUT Service started successfully!
    echo Check the console window for service logs
    echo ================================================================
) else (
    echo ERROR: Service failed to start
)

echo.
pause
