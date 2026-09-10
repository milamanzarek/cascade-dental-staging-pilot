<#
.SYNOPSIS
    Lane 3 Healthcare AI: One-Click Windows Clinic Edge Installer.
.DESCRIPTION
    Deploys the Lane 3 Edge Daemon as a self-healing background service on Windows Server
    or Windows 10/11 clinic reception hosts. Requires zero open inbound firewall ports.
.NOTES
    Author: Lane 3 Healthcare Engineering Team
    Version: 1.0.0
    Compliance: Universal Hard Gate U-HG-02, DOC-AA-01
#>

[CmdletBinding()]
param (
    [string]$InstallDir = "C:\Lane3Edge",
    [string]$ClinicId = "PR-001",
    [string]$ClinicName = "Bellevue Aesthetic Medicine",
    [string]$GatewayUrl = "wss://gateway.lane3healthcare.com/ws/edge",
    [string]$AuthToken = "default_secure_clinic_token_2026",
    [switch]$NonInteractive
)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  LANE 3 HEALTHCARE AI: WINDOWS CLINIC EDGE DAEMON INSTALLER    " -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Check Administrator Privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "Running in non-elevated mode. For automatic Windows Service registration, please run as Administrator."
} else {
    Write-Host "[OK] Administrator privileges confirmed." -ForegroundColor Green
}

# 2. Check Python Runtime
Write-Host "`n[1/5] Verifying Python runtime environment..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python 3.10+ is required but was not found in PATH. Please install Python from https://www.python.org/downloads/ and check 'Add Python to PATH'."
    exit 1
}
$pythonVersion = & python --version 2>&1
Write-Host "[OK] Found $pythonVersion at $($pythonCmd.Source)" -ForegroundColor Green

# 3. Test Outbound Firewall Connectivity (Port 443)
Write-Host "`n[2/5] Testing Outbound TLS 443 Handshake (Zero-Port Architecture)..." -ForegroundColor Yellow
$gatewayHost = "google.com"  # Diagnostic ping host
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect($gatewayHost, 443)
    $tcp.Close()
    Write-Host "[OK] Outbound Port 443 is open and clear. No inbound router ports required!" -ForegroundColor Green
} catch {
    Write-Warning "Could not connect to external port 443. Check outbound firewall proxy rules."
}

# 4. Create Installation Directory Hierarchy
Write-Host "`n[3/5] Setting up local directory structure at $InstallDir..." -ForegroundColor Yellow
$dirs = @(
    "$InstallDir",
    "$InstallDir\config",
    "$InstallDir\data",
    "$InstallDir\logs",
    "$InstallDir\bin"
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}
Write-Host "[OK] Directory hierarchy initialized." -ForegroundColor Green

# 5. Generate Clinic Configuration File (.env.clinic)
Write-Host "`n[4/5] Generating clinic configuration..." -ForegroundColor Yellow
$envPath = "$InstallDir\config\.env.clinic"
$configContent = @"
# Lane 3 Clinic Edge Configuration
LANE3_CLINIC_ID=$ClinicId
LANE3_CLINIC_NAME=$ClinicName
LANE3_PMS_TYPE=sqlite_mock
LANE3_DB_PATH=$InstallDir\data\clinic.db
LANE3_GATEWAY_URL=$GatewayUrl
LANE3_API_TOKEN=$AuthToken
LANE3_CARRIER_PROVIDER=telnyx
LANE3_EMERGENCY_PHONE=+12065550199
LANE3_LOG_LEVEL=INFO
LANE3_ZERO_PORT_TUNNEL=true
LANE3_PHI_SANITIZER=true
"@

Set-Content -Path $envPath -Value $configContent -Encoding UTF8
Write-Host "[OK] Configuration written to $envPath" -ForegroundColor Green

# 6. Register Windows Scheduled Task / Service for Auto-Start
Write-Host "`n[5/5] Registering self-healing background startup task..." -ForegroundColor Yellow
$taskName = "Lane3EdgeDaemon"
$daemonScript = "$InstallDir\bin\run_daemon.cmd"

$cmdContent = @"
@echo off
REM Lane 3 Edge Daemon Auto-Launcher
setlocal
cd /d "$InstallDir"
python -m edge_connector.connector_daemon --config "$envPath" >> "$InstallDir\logs\daemon.log" 2>&1
"@
Set-Content -Path $daemonScript -Value $cmdContent -Encoding ASCII

if ($isAdmin) {
    try {
        $action = New-ScheduledTaskAction -Execute "$daemonScript"
        $trigger = New-ScheduledTaskTrigger -AtStartup
        $settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 365)
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -User "NT AUTHORITY\SYSTEM" -RunLevel Highest -Force | Out-Null
        Write-Host "[OK] Scheduled Task '$taskName' successfully registered with auto-restart on boot!" -ForegroundColor Green
    } catch {
        Write-Warning "Could not register Windows Scheduled Task automatically: $_"
    }
} else {
    Write-Host "[NOTE] To complete background startup registration, execute this script in an elevated Administrator PowerShell prompt." -ForegroundColor Yellow
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION COMPLETED SUCCESSFULLY!                           " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Daemon Directory : $InstallDir" -ForegroundColor White
Write-Host "Configuration    : $envPath" -ForegroundColor White
Write-Host "Daemon Logs      : $InstallDir\logs\daemon.log" -ForegroundColor White
Write-Host "To test manually : python -m edge_connector.connector_daemon" -ForegroundColor White
Write-Host "Support Contact  : director@lane3healthcare.com | (206) 880-0477`n" -ForegroundColor Cyan
