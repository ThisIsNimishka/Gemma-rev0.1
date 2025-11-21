@echo off
echo ================================================================
echo  SUT Service Uninstaller
echo  Removing service and scheduled task...
echo ================================================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: This script requires Administrator privileges!
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

set INSTALL_DIR=C:\Program Files\SUTService

REM Stop the service if running
echo Stopping SUTService if running...
taskkill /F /IM SUTService.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Delete scheduled task
echo Removing scheduled task...
schtasks /delete /tn "SUTService" /f >nul 2>&1

REM Delete installation directory
if exist "%INSTALL_DIR%" (
    echo Deleting installation directory: %INSTALL_DIR%
    rd /s /q "%INSTALL_DIR%"
)

echo.
echo ================================================================
echo Uninstallation completed successfully!
echo.
echo SUT Service has been removed from your system.
echo ================================================================
echo.
pause
