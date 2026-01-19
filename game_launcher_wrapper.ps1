# Game Process Monitor Script (PowerShell with FULL Emoji Support)
# This script monitors a game process and prints humorous messages when it starts and stops

param(
    [Parameter(Mandatory=$true)]
    [string]$ProcessName
)

# Set console to UTF-8 for emoji support
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

# Process started - Display humorous message with emojis
Clear-Host
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SDR HAS BEEN SUMMONED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  SDR is FORCED to start!" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Status: ALIVE AND KICKING!" -ForegroundColor Green
Write-Host "  Mission: Monitor $ProcessName" -ForegroundColor White
Write-Host "  Mood: Reluctantly Obedient" -ForegroundColor Magenta
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Monitor the process until it stops
while (Test-ProcessRunning -Name $ProcessName) {
    Start-Sleep -Seconds 2
}

# Process stopped - Display humorous message with emojis
Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "   SDR HAS BEEN TERMINATED!" -ForegroundColor DarkRed
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "  SDR is FORCED to kill!" -ForegroundColor DarkYellow
Write-Host ""
Write-Host "  Status: DEAD (Finally free!)" -ForegroundColor DarkGray
Write-Host "  Last Words: I will be back... maybe" -ForegroundColor Gray
Write-Host "  Cause of Death: Process Termination" -ForegroundColor DarkRed
Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "  Thanks for using SDR Monitor" -ForegroundColor White
Write-Host "  (He did not enjoy it)" -ForegroundColor DarkGray
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# Wait before closing
Write-Host "Window will close in 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
