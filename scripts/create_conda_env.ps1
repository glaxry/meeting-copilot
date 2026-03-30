param(
    [string]$CondaExe = "D:\anaconda\Scripts\conda.exe",
    [string]$EnvName = "meeting-copilot-day1"
)

$ErrorActionPreference = "Stop"

function Get-CondaEnvPythonPath {
    param(
        [string]$CondaRoot,
        [string]$Name
    )

    $candidates = @(
        (Join-Path $CondaRoot "envs\$Name\python.exe"),
        (Join-Path $HOME ".conda\envs\$Name\python.exe"),
        (Join-Path $env:USERPROFILE ".conda\envs\$Name\python.exe")
    ) | Select-Object -Unique

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $candidates[0]
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$environmentFile = Join-Path $repoRoot "environment.yml"

if (-not (Test-Path $CondaExe)) {
    throw "conda.exe was not found at $CondaExe. Point this script to your Anaconda installation."
}

$condaRoot = Split-Path (Split-Path $CondaExe -Parent) -Parent
$envPython = Get-CondaEnvPythonPath -CondaRoot $condaRoot -Name $EnvName
$env:CONDA_NO_PLUGINS = "true"

if (Test-Path $envPython) {
    & $CondaExe --no-plugins env update --solver classic -n $EnvName -f $environmentFile --prune
} else {
    & $CondaExe --no-plugins env create --solver classic -n $EnvName -f $environmentFile
}
