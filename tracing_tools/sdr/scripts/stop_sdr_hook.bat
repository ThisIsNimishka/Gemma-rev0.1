@echo off
REM === SDR Stop Script (Hook Version) ===

set "SDR_DIR=C:\OWR\SDR\Intel(R)SystemDataRecorder_OneBKC\SDRBinaries\SDRApplication\SDRTrayAppCmdLine"

echo Stopping SDR, will take sometime to generate report.
pushd "%SDR_DIR%" || (echo ERROR: SDR directory not found & exit /b 1)

SDRTrayAppCmdLine.exe --stop

set "EC=%ERRORLEVEL%"
echo ExitCode=%EC%

if %EC% NEQ 0 (
  echo SDR STOP failed with error code %EC%
) else (
  echo SDR STOP successful
)

popd


:copy_reports
::echo Copying reports
set "REPORT_SRC=C:\ProgramData\Intel Corporation\SystemDataRecorder\SDR\Reports"
set "REPORT_DEST=%~dp0..\reports"

if not exist "%REPORT_DEST%" mkdir "%REPORT_DEST%"

::echo Source: "%REPORT_SRC%"
::echo Dest:   "%REPORT_DEST%"

xcopy /D /Y /I /S "%REPORT_SRC%\*" "%REPORT_DEST%" >nul
if %ERRORLEVEL% EQU 0 (
    echo Reports generated successfully.
) else (
    echo [WARNING] Failed to copy reports (ExitCode=%ERRORLEVEL%).
)
exit /b %EC%
