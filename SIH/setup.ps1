param(
    [switch]$ResetDatabase,
    [switch]$SkipModels
)

$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $venvPython)) {
        $basePython = Get-Command python -ErrorAction SilentlyContinue
        if (-not $basePython) {
            $launcher = Get-Command py -ErrorAction SilentlyContinue
            if ($launcher) {
                & $launcher.Source -3 -m venv '.venv'
            } else {
                throw 'Python 3.10 or newer is required. Install Python, then run setup.ps1 again.'
            }
        } else {
            & $basePython.Source -m venv '.venv'
        }
    }
    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw 'The Python virtual environment could not be created.'
    }

    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r 'requirements.txt'
    if (-not (Test-Path -LiteralPath '.env')) {
        Copy-Item -LiteralPath '.env.example' -Destination '.env'
    }

    $dataArgs = @('tools\prepare_local_data.py')
    if ($ResetDatabase) { $dataArgs += '--reset' }
    & $venvPython @dataArgs

    if (-not $SkipModels) {
        $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
        $ollamaPath = if ($ollamaCommand) { $ollamaCommand.Source } else { $null }
        if (-not $ollamaPath) {
            $commonOllama = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
            if (Test-Path -LiteralPath $commonOllama) {
                $ollamaPath = $commonOllama
            } else {
                $winget = Get-Command winget -ErrorAction SilentlyContinue
                if (-not $winget) {
                    throw 'Ollama is required. Install it from https://ollama.com/download and run setup.ps1 again.'
                }
                & $winget.Source install --exact --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
                if (-not (Test-Path -LiteralPath $commonOllama)) {
                    throw 'Ollama installation did not complete. Run setup.ps1 again after installing Ollama.'
                }
                $ollamaPath = $commonOllama
            }
        }

        try {
            Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3 | Out-Null
        } catch {
            Start-Process -FilePath $ollamaPath -ArgumentList 'serve' -WindowStyle Hidden
            $ready = $false
            for ($attempt = 0; $attempt -lt 30; $attempt++) {
                Start-Sleep -Seconds 1
                try {
                    Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2 | Out-Null
                    $ready = $true
                    break
                } catch {}
            }
            if (-not $ready) { throw 'Ollama did not start within 30 seconds.' }
        }

        $modelManifest = Get-Content -Raw -LiteralPath 'models\manifest.json' | ConvertFrom-Json
        foreach ($model in $modelManifest.models) {
            Write-Host "Preparing $($model.name)..."
            & $ollamaPath pull $model.name
            if ($LASTEXITCODE -ne 0) { throw "Could not download $($model.name)." }
        }
        & $venvPython 'tools\cache_embedding_model.py'
    }

    Write-Host ''
    Write-Host 'StatSkill AI setup is complete.' -ForegroundColor Green
    Write-Host 'Run .\run.ps1 and open http://127.0.0.1:8000'
} finally {
    Pop-Location
}
