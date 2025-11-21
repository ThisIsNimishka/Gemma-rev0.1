@echo off
echo ================================================================
echo  SUT Service Tester
echo  Testing if service is running and responding...
echo ================================================================
echo.

REM Check if service process is running
tasklist /FI "IMAGENAME eq SUTService.exe" 2>nul | find /I "SUTService.exe" >nul
if errorlevel 1 (
    echo [FAIL] SUT Service is NOT running
    echo        Please start the service first
    echo.
    pause
    exit /b 1
)

echo [OK] SUT Service process is running
echo.

REM Test health endpoint using curl or powershell
echo Testing service endpoints...
echo.

REM Use PowerShell to test HTTP endpoint
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8080/health' -UseBasicParsing -TimeoutSec 5; Write-Host '[OK] Health check: Service responding'; Write-Host ''; Write-Host 'Response:'; $response.Content | ConvertFrom-Json | ConvertTo-Json } catch { Write-Host '[FAIL] Could not connect to service on port 8080'; Write-Host 'Error:' $_.Exception.Message }"

echo.
echo ================================================================
echo Test completed
echo.
echo If health check passed, service is ready to accept commands
echo If failed, check:
echo   - Service is running with admin privileges
echo   - Port 8080 is not blocked by firewall
echo   - No other application is using port 8080
echo ================================================================
echo.
pause
