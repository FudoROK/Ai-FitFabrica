param(
    [string]$OutputPath = "backend-deploy.tar.gz"
)

$ErrorActionPreference = "Stop"

$excludeArgs = @(
    "--exclude=.git",
    "--exclude=.venv",
    "--exclude=node_modules",
    "--exclude=apps/web/node_modules",
    "--exclude=apps/web/.next",
    "--exclude=tmp",
    "--exclude=output",
    "--exclude=test-assets",
    "--exclude=backend-deploy.tar.gz",
    "--exclude=.env",
    "--exclude=.env.*",
    "--exclude=apps/web/.env.local",
    "--exclude=service-account.json",
    "--exclude=secrets",
    "--exclude=*.pem",
    "--exclude=*.key",
    "--exclude=*.p12"
)

if (Test-Path -LiteralPath $OutputPath) {
    Remove-Item -LiteralPath $OutputPath -Force
}

tar @excludeArgs -czf $OutputPath .

$envEntries = tar -tzf $OutputPath | Select-String -Pattern '(^|/)\.env($|\.|/)|service-account\.json|(^|/)secrets/'
if ($envEntries) {
    Remove-Item -LiteralPath $OutputPath -Force -ErrorAction SilentlyContinue
    throw "Deployment archive contains local env or secret files."
}

Write-Output "Created $OutputPath"
