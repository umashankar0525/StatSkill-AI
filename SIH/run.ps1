param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$env:STATSKILL_PORT = "$Port"
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Project setup is incomplete. Run .\setup.ps1 first.'
}
Push-Location -LiteralPath $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath 'igot_demo.db')) {
        & $projectPython 'tools\prepare_local_data.py'
    }
    & $projectPython server.py
} finally { Pop-Location }
