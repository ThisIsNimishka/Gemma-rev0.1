@echo off
set "SDR_PATH=C:\OWR\SDR\Intel(R)SystemDataRecorder_OneBKC\SDRBinaries\SDRApplication\SDRTrayAppCmdLine\SDRTrayAppCmdLine.exe"

echo 1) Enable log collection (pre-req)
"%SDR_PATH%" --log-collection --enable=Yes

echo 2) Start (Debug mode)
"%SDR_PATH%" --start --testcase-id=SDR-TEST --user-name=%USERNAME% --team-name=SIV test-name=AutomationTest test-domain=SIVdomain --run-type=Debug --log-collectors=WLAN,PnP

echo 3) Mark step
"%SDR_PATH%" --test-step="Test Step Marker"

timeout /t 5

echo 4) Stop
"%SDR_PATH%" --stop

