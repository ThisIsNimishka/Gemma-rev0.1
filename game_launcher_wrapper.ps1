# Game Process Monitor Script
# This script monitors a game process and prints status updates.

param(
    [Parameter(Mandatory=$true)]
    [string]$ProcessName
)

# Set console to UTF-8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Set window title
$Host.UI.RawUI.WindowTitle = "SDR Monitor - Watching $ProcessName"

# Function to check if process is running
function Test-ProcessRunning {
    param([string]$Name)
    return (Get-Process -Name $Name.Replace('.exe', '') -ErrorAction SilentlyContinue) -ne $null
}

# Wait for the process to start
Write-Host "`nWaiting for $ProcessName to start..." -ForegroundColor Yellow

while (-not (Test-ProcessRunning -Name $ProcessName)) {
    Start-Sleep -Milliseconds 500
}

# Process started
Clear-Host
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SDR MONITORING ACTIVE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  SDR monitoring is now active." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Status: Active" -ForegroundColor Green
Write-Host "  Monitoring Process: $ProcessName" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

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
Write-Host "  SDR process monitoring finished." -ForegroundColor DarkYellow
Write-Host ""
Write-Host "  Status: Inactive" -ForegroundColor DarkGray
Write-Host "  Reason: Monitored process ended." -ForegroundColor DarkRed
Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "  SDR Monitor has finished." -ForegroundColor White
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# Wait before closing
Write-Host "Window will close in 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Wait before closing
Write-Host "Window will close in 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
