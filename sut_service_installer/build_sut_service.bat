@echo off
echo ================================================================
echo  SUT Service Builder
echo  Building executable with PyInstaller...
echo ================================================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller not found!
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Build the executable
echo Building SUTService.exe...
pyinstaller --onefile --uac-admin --console --name SUTService gemma_sut_service_improved_3.1.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ================================================================
echo Build completed successfully!
echo.
echo Executable location: dist\SUTService.exe
echo.
echo Next steps:
echo   1. Test the service: cd dist ^&^& SUTService.exe
echo   2. Install as auto-start: run install_sut_service.bat
echo ================================================================
echo.
pause
