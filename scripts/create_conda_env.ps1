param(
    [string]$CondaExe = ".miniconda3\\Scripts\\conda.exe",
    [string]$EnvName = "meeting-copilot-day1"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$condaPath = Join-Path $repoRoot $CondaExe
$environmentFile = Join-Path $repoRoot "environment.yml"

if (-not (Test-Path $condaPath)) {
    throw "conda.exe was not found at $condaPath. Install Miniconda first."
}

$envExists = & $condaPath env list | Select-String -SimpleMatch $EnvName
if ($envExists) {
    & $condaPath env update -n $EnvName -f $environmentFile --prune
} else {
    & $condaPath env create -n $EnvName -f $environmentFile
}
