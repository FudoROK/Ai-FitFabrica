[CmdletBinding()]
param(
    [string[]]$PytestArgs = @(),
    [switch]$SkipArchitecture,
    [switch]$SkipCompile,
    [switch]$SkipPytest
)

$ErrorActionPreference = "Stop"
$script:RepoRoot = $null
$script:PythonCommand = $null

function Resolve-RepoRoot {
    $candidate = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
    $requiredPaths = @(
        (Join-Path $candidate "AGENTS.md"),
        (Join-Path $candidate "src"),
        (Join-Path $candidate "scripts")
    )

    foreach ($requiredPath in $requiredPaths) {
        if (-not (Test-Path $requiredPath)) {
            throw "Repository root validation failed. Missing required path: $requiredPath"
        }
    }

    return $candidate
}

function Resolve-PythonCommand {
    $venvPython = Join-Path $script:RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $pythonCommand = Get-Command python -ErrorAction Stop
    return $pythonCommand.Source
}

function Invoke-PythonStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Host "[validate_repo] $Label"
    & $script:PythonCommand @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

$script:RepoRoot = Resolve-RepoRoot
$script:PythonCommand = Resolve-PythonCommand

Push-Location $script:RepoRoot
try {
    Write-Host "[validate_repo] Repo root: $script:RepoRoot"
    Write-Host "[validate_repo] Python: $script:PythonCommand"

    if (-not $SkipArchitecture) {
        Invoke-PythonStep -Label "architecture check" -Arguments @("scripts/check_architecture.py")
    }

    if (-not $SkipCompile) {
        Invoke-PythonStep -Label "compileall" -Arguments @("-m", "compileall", "src")
    }

    if (-not $SkipPytest) {
        $pytestArguments = @("-m", "pytest", "-q") + $PytestArgs
        Invoke-PythonStep -Label "pytest" -Arguments $pytestArguments
    }
}
finally {
    Pop-Location
}
