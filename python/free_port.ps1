# Free a TCP listen port on Windows. Exit 0 when free, 2 when still occupied.
param(
  [Parameter(Mandatory = $true)]
  [int]$Port
)

$ErrorActionPreference = 'SilentlyContinue'

function Get-ListenPids {
  $pids = [System.Collections.Generic.HashSet[int]]::new()
  $lines = netstat -ano -p TCP 2>$null
  foreach ($line in $lines) {
    if ($line -notmatch 'LISTENING') { continue }
    if ($line -match (":$Port\s+\S+\s+LISTENING\s+(\d+)\s*$")) {
      [void]$pids.Add([int]$Matches[1])
    }
  }
  return @($pids)
}

$pids = Get-ListenPids
if ($pids.Count -eq 0) {
  Write-Host "  port $Port already free"
  exit 0
}

foreach ($procId in $pids) {
  if ($procId -le 0) { continue }
  $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
  $name = if ($proc) { $proc.ProcessName } else { '?' }
  Write-Host ("  kill PID {0} ({1})" -f $procId, $name)
  Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Milliseconds 400

Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
  Where-Object {
    $_.CommandLine -and
    ($_.CommandLine -match 'manage\.py') -and
    ($_.CommandLine -match 'runserver') -and
    ($_.CommandLine -match ":$Port")
  } |
  ForEach-Object {
    Write-Host ("  kill leftover python PID {0}" -f $_.ProcessId)
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }

Start-Sleep -Milliseconds 300
$left = Get-ListenPids
if ($left.Count -gt 0) {
  Write-Host "  port $Port still in use"
  exit 2
}

Write-Host "  port $Port freed"
exit 0
