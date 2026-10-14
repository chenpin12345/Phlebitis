$ErrorActionPreference = 'Stop'
# Stops only this project's servers: a process listening on 8765 (workbench) or 8000 (LINE)
# whose command line is "-m src workbench" or "-m src serve". Running training workers are not killed;
# they finish or are marked interrupted on the next start.
$stopped = 0
foreach ($port in 8765, 8000) {
    $owners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($owner in $owners) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$owner"
        if (-not $process -or $process.CommandLine -notmatch '-m src (workbench|serve)') {
            Write-Host "Port $port is used by another program (PID $owner); left running."
            continue
        }
        $ids = @($owner)
        $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($process.ParentProcessId)"
        if ($parent -and $parent.CommandLine -match '-m src (workbench|serve)') { $ids += $parent.ProcessId }
        Stop-Process -Id $ids -Force
        Write-Host "Stopped port $port (PID $($ids -join ', '))."
        $stopped++
    }
}
if (-not $stopped) { Write-Host 'No workbench or LINE service of this project is running.' }
