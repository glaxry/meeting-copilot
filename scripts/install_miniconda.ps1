param(
    [string]$InstallerUrl = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe",
    [string]$InstallDir = ".miniconda3"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$installerDir = Join-Path $repoRoot ".cache"
$installerPath = Join-Path $installerDir "Miniconda3-latest-Windows-x86_64.exe"
$targetDir = Join-Path $repoRoot $InstallDir

New-Item -ItemType Directory -Force -Path $installerDir | Out-Null

Write-Host "Downloading Miniconda installer to $installerPath"
Invoke-WebRequest -Uri $InstallerUrl -OutFile $installerPath

Write-Host "Installing Miniconda to $targetDir"
Start-Process -FilePath $installerPath -ArgumentList "/InstallationType=JustMe", "/RegisterPython=0", "/S", "/D=$targetDir" -Wait -NoNewWindow

Write-Host "Miniconda installation finished."
