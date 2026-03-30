param(
    [string]$CondaRoot = ".miniconda3",
    [string]$EnvName = "meeting-copilot-day1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$pythonPath = Join-Path $repoRoot "$CondaRoot\envs\$EnvName\python.exe"

if (-not (Test-Path $pythonPath)) {
    throw "Conda environment python was not found at $pythonPath. Create the environment first."
}

& $pythonPath -m uvicorn meeting_copilot.app:app --app-dir (Join-Path $repoRoot "python") --host 127.0.0.1 --port $Port --reload
