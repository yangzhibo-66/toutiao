param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$RootDir = $PSScriptRoot
$FrontendRoot = Get-ChildItem -LiteralPath $RootDir -Directory |
    Where-Object { $_.Name -like "03-*" } |
    Select-Object -First 1

if (-not $FrontendRoot) {
    throw "Frontend parent directory was not found under: $RootDir"
}

$FrontendDir = Join-Path $FrontendRoot.FullName "xwzx-news"
$BackendDir = Join-Path $RootDir "fastApiProject"
$VenvDir = Join-Path $BackendDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Require-Command {
    param(
        [string]$Name,
        [string]$InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command not found: $Name. $InstallHint"
    }
}

function Get-PythonCommand {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @("py", "-3")
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @("python")
    }

    throw "Python was not found. Please install Python 3 first."
}

function Invoke-Python {
    param([string[]]$Arguments)

    $pythonCommand = Get-PythonCommand
    $exe = $pythonCommand[0]
    $baseArgs = @()
    if ($pythonCommand.Count -gt 1) {
        $baseArgs = $pythonCommand[1..($pythonCommand.Count - 1)]
    }

    & $exe @baseArgs @Arguments
}

function Get-PythonLaunchExpression {
    $pythonCommand = Get-PythonCommand
    return ($pythonCommand | ForEach-Object {
        if ($_ -match '\s') {
            "'$_'"
        }
        else {
            $_
        }
    }) -join " "
}

function Start-AppWindow {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command
    )

    $windowCommand = @"
`$Host.UI.RawUI.WindowTitle = '$Title'
Set-Location -LiteralPath '$WorkingDirectory'
$Command
"@

    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $windowCommand
    )
}

if (-not (Test-Path -LiteralPath $FrontendDir)) {
    throw "Frontend directory does not exist: $FrontendDir"
}
if (-not (Test-Path -LiteralPath $BackendDir)) {
    throw "Backend directory does not exist: $BackendDir"
}

Require-Command "npm" "Please install Node.js first."

if (-not $SkipInstall) {
    Write-Step "Checking frontend dependencies"
    if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules"))) {
        Push-Location $FrontendDir
        try {
            npm install
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "Frontend node_modules exists; skipping npm install."
    }

    Write-Step "Checking backend virtual environment"
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Invoke-Python @("-m", "venv", $VenvDir)
    }
    else {
        Write-Host "Backend .venv exists; skipping venv creation."
    }

    Write-Step "Installing/updating backend dependencies"
    & $VenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")
}

$BackendPython = if (Test-Path -LiteralPath $VenvPython) {
    "& '$VenvPython'"
}
else {
    Get-PythonLaunchExpression
}

Write-Step "Starting backend: http://127.0.0.1:8000"
Start-AppWindow `
    -Title "toutiao backend API" `
    -WorkingDirectory $BackendDir `
    -Command "$BackendPython -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

Write-Step "Starting frontend: http://127.0.0.1:5173"
Start-AppWindow `
    -Title "toutiao frontend" `
    -WorkingDirectory $FrontendDir `
    -Command "npm run dev -- --host 127.0.0.1 --port 5173"

Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:5173"

Write-Host ""
Write-Host "Started. Close the frontend/backend windows to stop the services." -ForegroundColor Green
