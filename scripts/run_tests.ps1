param(
    [string]$CondaRoot = "D:\anaconda",
    [string]$EnvName = "meeting-copilot-day1"
)

$ErrorActionPreference = "Stop"

function Get-CondaEnvPythonPath {
    param(
        [string]$Root,
        [string]$Name
    )

    $candidates = @(
        (Join-Path $Root "envs\$Name\python.exe"),
        (Join-Path $HOME ".conda\envs\$Name\python.exe"),
        (Join-Path $env:USERPROFILE ".conda\envs\$Name\python.exe")
    ) | Select-Object -Unique

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Conda environment python was not found in any expected location for $Name."
}

$pythonPath = Get-CondaEnvPythonPath -Root $CondaRoot -Name $EnvName

& $pythonPath -m pytest
