param(
    [string]$CondaRoot = "D:\anaconda",
    [string]$EnvName = "meeting-copilot-day1",
    [int]$Port = 8000
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

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$pythonPath = Get-CondaEnvPythonPath -Root $CondaRoot -Name $EnvName

& $pythonPath -m uvicorn meeting_copilot.app:app --app-dir (Join-Path $repoRoot "python") --host 127.0.0.1 --port $Port --reload
