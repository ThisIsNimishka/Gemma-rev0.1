@echo off
echo ================================================================
echo  SUT Service Installer
echo  Installing as Windows auto-start service...
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

REM Check if executable exists
if not exist "dist\SUTService.exe" (
    echo ERROR: SUTService.exe not found in dist folder!
    echo Please run build_sut_service.bat first
    pause
    exit /b 1
)

REM Create installation directory
set INSTALL_DIR=C:\Program Files\SUTService
echo Creating installation directory: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy executable
echo Copying SUTService.exe to %INSTALL_DIR%...
copy /Y "dist\SUTService.exe" "%INSTALL_DIR%\"
if errorlevel 1 (
    echo ERROR: Failed to copy executable
    pause
    exit /b 1
)

REM Create scheduled task for auto-start
echo Creating scheduled task for auto-start...
schtasks /create /tn "SUTService" /tr "\"%INSTALL_DIR%\SUTService.exe\"" /sc onstart /ru SYSTEM /rl highest /f

if errorlevel 1 (
    echo ERROR: Failed to create scheduled task
    pause
    exit /b 1
)

echo.
echo ================================================================
echo Installation completed successfully!
echo.
echo Service Details:
echo   - Location: %INSTALL_DIR%\SUTService.exe
echo   - Auto-start: YES (runs at system startup)
echo   - Privileges: Administrator (via scheduled task)
echo   - Port: 8080 (default)
echo.
echo To start service now: run start_sut_service.bat
echo To stop service: run stop_sut_service.bat
echo To uninstall: run uninstall_sut_service.bat
echo ================================================================
echo.
pause
