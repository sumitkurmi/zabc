
# AI-Assisted Network Complaint Portal
# Windows hostel network configuration helper
# Preview only. This script does not apply network changes.

$ErrorActionPreference = "Stop"

$Gateway = "172.31.68.1"
$SubnetMask = "255.255.254.0"
$PrefixLength = 23
$DnsServers = @("172.31.100.6", "172.31.100.7", "172.31.100.8")
$ProxyHosts = @("172.31.100.27", "172.31.102.29")
$ProxyPort = 3128

function Get-RoomIPAddress {
    param([int]$RoomNumber)

    $floor = [math]::Floor($RoomNumber / 100)
    $roomOnFloor = $RoomNumber % 100

    if ($floor -lt 1 -or $floor -gt 13 -or
        $roomOnFloor -lt 1 -or $roomOnFloor -gt 28) {
        throw "Invalid room number. Valid rooms are 101-128, 201-228, ... 1301-1328."
    }

    $roomIndex = (($floor - 1) * 28) + ($roomOnFloor - 1)

    # Start at 172.31.68.60 and skip 172.31.68.255.
    $ipNumber = [uint64]([System.Net.IPAddress]::Parse("172.31.68.0").GetAddressBytes()[0]) * 16777216 +
                [uint64]([System.Net.IPAddress]::Parse("172.31.68.0").GetAddressBytes()[1]) * 65536 +
                [uint64]([System.Net.IPAddress]::Parse("172.31.68.0").GetAddressBytes()[2]) * 256 +
                [uint64]([System.Net.IPAddress]::Parse("172.31.68.0").GetAddressBytes()[3])

    $ipNumber += 60 + $roomIndex

    # Skip the broadcast address at 172.31.68.255.
    if ($ipNumber -eq [uint64]([System.Net.IPAddress]::Parse("172.31.68.255").GetAddressBytes()[0]) * 16777216 +
                      [uint64]([System.Net.IPAddress]::Parse("172.31.68.255").GetAddressBytes()[1]) * 65536 +
                      [uint64]([System.Net.IPAddress]::Parse("172.31.68.255").GetAddressBytes()[2]) * 256 +
                      [uint64]([System.Net.IPAddress]::Parse("172.31.68.255").GetAddressBytes()[3])) {
        $ipNumber++
    }

    $bytes = @(
        [byte](($ipNumber -shr 24) -band 255),
        [byte](($ipNumber -shr 16) -band 255),
        [byte](($ipNumber -shr 8) -band 255),
        [byte]($ipNumber -band 255)
    )

    return ([System.Net.IPAddress]::new([byte[]]$bytes)).ToString()
}

Write-Host ""
Write-Host "=== Hostel Network Configuration Preview ===" -ForegroundColor Cyan
Write-Host "Hostel: C Block"

$roomInput = Read-Host "Enter your room number (e.g. 204)"

[int]$roomNumber = 0
if (-not [int]::TryParse($roomInput, [ref]$roomNumber)) {
    Write-Host "Room number must be numeric." -ForegroundColor Red
    exit 1
}

try {
    $ipAddress = Get-RoomIPAddress -RoomNumber $roomNumber
}
catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

try {
    $adapters = @(Get-NetAdapter -ErrorAction Stop |
        Where-Object { $_.Status -eq "Up" })
}
catch {
    Write-Host "Could not detect network adapters. Run this script on Windows." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Room: $roomNumber"
Write-Host "Proposed IP: $ipAddress"
Write-Host "Subnet mask: $SubnetMask"
Write-Host "Prefix length: /$PrefixLength"
Write-Host "Gateway: $Gateway"
Write-Host "DNS servers: $($DnsServers -join ', ')"
Write-Host "Proxy endpoints: $($ProxyHosts -join ', '):$ProxyPort"

Write-Host ""
Write-Host "Active network adapters:" -ForegroundColor Cyan

if ($adapters.Count -eq 0) {
    Write-Host "No active network adapters were detected." -ForegroundColor Red
}
else {
    $adapters | Format-Table -Property Name, InterfaceDescription, Status -AutoSize
}

Write-Host ""
Write-Host "PREVIEW ONLY: no network settings have been changed." -ForegroundColor Yellow
Write-Host "Network changes are not implemented in this version."
