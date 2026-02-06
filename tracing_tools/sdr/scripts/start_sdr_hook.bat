@echo off
REM === SDR Start Script (v2.0.1003, hardened) ===
REM Usage: start_sdr_hook.bat [TestCaseID] [UserName] [QDF] [TestName] [TeamName]

setlocal EnableExtensions EnableDelayedExpansion

REM --- Config ---
set "SDR_DIR=C:\OWR\SDR\Intel(R)SystemDataRecorder_OneBKC\SDRBinaries\SDRApplication\SDRTrayAppCmdLine"

REM --- Inputs (with safe defaults) ---
set "TESTCASE_ID=%~1"
if "%TESTCASE_ID%"=="" set "TESTCASE_ID=PSPV-TC-10391"

set "USERNAME=%~2"
if "%USERNAME%"=="" set "USERNAME=UserX"

set "QDF=%~3"
if "%QDF%"=="" set "QDF=L173"

set "TEST_NAME=%~4"
if "%TEST_NAME%"=="" set "TEST_NAME=SIV_Automation"


set "TEAM_NAME=%~5"
if "%TEAM_NAME%"=="" set "TEAM_NAME=SIV_Automation"

REM --- Sanitize (strip any embedded quotes) ---
for %%V in (TESTCASE_ID USERNAME QDF TEST_NAME TEAM_NAME) do (
  set "TMP=!%%V:\"=!"
  set "%%V=!TMP!"
)

echo Starting SDR in Test (debug-like) Mode...
echo DIR: %SDR_DIR%
echo ID: %TESTCASE_ID%, User: %USERNAME%, QDF: %QDF%

pushd "%SDR_DIR%" || (echo ERROR: SDR directory not found & exit /b 1)

REM Create logs directory relative to script folder (..\reports)
set "LOG_DIR=%~dp0..\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Ensure log collection is ON
SDRTrayAppCmdLine.exe --log-collection --enable=Yes

REM Build a single-line start command with explicit quoting
set "CMD=SDRTrayAppCmdLine.exe --start --testcase-id="%TESTCASE_ID%" --user-name="%USERNAME%" --team-name="%TEAM_NAME%" --qdf="%QDF%" --test-domain="SIV" --test-name="%TEST_NAME%" --log-collectors="WLAN,PnP" --log-path="%LOG_DIR%" --run-type=Debug"

echo Running:
echo %CMD%
%CMD%
set "EC=%ERRORLEVEL%"
echo ExitCode=%EC%

if %EC% NEQ 0 (
  echo [ERROR] SDR START failed with ExitCode=%EC%
  echo Tips:
  echo   - If it says 'Invalid input --serialno', try typing the flag manually to avoid non-ASCII dashes.
  echo   - Try the minimal one-liner without log-collectors/log-path to isolate the issue.
) else (
  echo SDR START successful
)

popd
endlocal
exit /b %EC%