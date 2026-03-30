param(
    [string]$CondaRoot = ".miniconda3",
    [string]$EnvName = "meeting-copilot-day1"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$pythonPath = Join-Path $repoRoot "$CondaRoot\envs\$EnvName\python.exe"

if (-not (Test-Path $pythonPath)) {
    throw "Conda environment python was not found at $pythonPath. Create the environment first."
}

& $pythonPath -m pytest
