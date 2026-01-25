# Game Process Monitor Script
# This script monitors a game process and manages the SDR (System Data Recorder) monitoring session.

param(
    [Parameter(Mandatory=$true)]
    [string]$ProcessName,
    
    [string]$TestCaseId = "PSPV-TC-10391",
    [string]$UserName = $env:USERNAME,
    [string]$LogCollectors = "WLAN,PnP,ETL",
    [string]$TestDomain = "",
    [string]$TestName = ""
)

# Set console to UTF-8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$SDR_PATH = "C:\OWR\SDR\Intel(R)SystemDataRecorder_OneBKC\SDRBinaries\SDRApplication\SDRTrayAppCmdLine\SDRTrayAppCmdLine.exe"

# Set window title
$Host.UI.RawUI.WindowTitle = "SDR Monitor - Watching $ProcessName"

# Function to check if process is running
function Test-ProcessRunning {
    param([string]$Name)
    return (Get-Process -Name $Name.Replace('.exe', '') -ErrorAction SilentlyContinue) -ne $null
}

Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host "1) Enable log collection (pre-req)" -ForegroundColor Yellow
if (Test-Path $SDR_PATH) {
    & $SDR_PATH --log-collection --enable=Yes
}

Write-Host "2) Starting SDR Monitoring..." -ForegroundColor Yellow
$StartArgs = @("--start", "--testcase-id=$TestCaseId", "--user-name=$UserName", "--team-name=SIV", "--run-type=Debug", "--log-collectors=$LogCollectors")

if ($TestDomain) {
    $StartArgs += "--test-domain=$TestDomain"
}
if ($TestName) {
    $StartArgs += "--test-name=$TestName"
}

Write-Host "Command: $SDR_PATH $($StartArgs -join ' ')" -ForegroundColor Gray

if (Test-Path $SDR_PATH) {
    & $SDR_PATH @StartArgs
} else {
    Write-Host "WARNING: SDRTrayAppCmdLine.exe not found at $SDR_PATH" -ForegroundColor Red
    Write-Host "Proceeding with game launch anyway..." -ForegroundColor Yellow
}
Write-Host "------------------------------------------------" -ForegroundColor Cyan

# Wait for the process to start
Write-Host "`nWaiting for $ProcessName to start..." -ForegroundColor Yellow

while (-not (Test-ProcessRunning -Name $ProcessName)) {
    Start-Sleep -Milliseconds 500
}

# Process started
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SDR MONITORING ACTIVE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Process $ProcessName detected." -ForegroundColor Yellow
Write-Host ""

if (Test-Path $SDR_PATH) {
    & $SDR_PATH --test-step="Process Started: $ProcessName"
}

# Monitor the process until it stops
while (Test-ProcessRunning -Name $ProcessName) {
    Start-Sleep -Seconds 2
}

# Process stopped
Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "   SDR MONITORING STOPPED" -ForegroundColor DarkRed
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "  Process $ProcessName has stopped." -ForegroundColor DarkYellow
Write-Host ""

Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host "Stopping SDR Monitoring..." -ForegroundColor Yellow
if (Test-Path $SDR_PATH) {
    & $SDR_PATH --test-step="Process Stopped: $ProcessName"
    & $SDR_PATH --stop
} else {
    Write-Host "SDRTrayAppCmdLine.exe was not found to stop the process." -ForegroundColor Red
}
Write-Host "------------------------------------------------" -ForegroundColor Cyan

# Wait before closing
Write-Host "Window will close in 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
