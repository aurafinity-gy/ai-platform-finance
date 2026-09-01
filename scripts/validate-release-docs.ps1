param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$requiredPaths = @(
    'compose.release.yaml',
    'README.md',
    'docs/runbooks/finance-runtime-config.md',
    'docs/runbooks/local-finance-migration.md',
    'docs/runbooks/staging-validation.md',
    'docs/runbooks/release-operations.md',
    'docs/runbooks/post-release.md',
    'docs/runbooks/deployment-manifest.md',
    'docs/runbooks/production-readiness-audit.md',
    'docs/runbooks/production-readiness-checklist.md'
    'docs/architecture/research-job-queue.md'
    'scripts/finance-smoke-test.ps1'
)

foreach ($relative in $requiredPaths) {
    $fullPath = Join-Path $RepositoryRoot $relative
    if (-not (Test-Path $fullPath)) {
        throw "Missing expected file: $relative"
    }
}

$readme = Get-Content -Path (Join-Path $RepositoryRoot 'README.md') -Raw
$requiredLinks = @(
    'docs/runbooks/finance-runtime-config.md',
    'docs/runbooks/local-finance-migration.md',
    'docs/runbooks/staging-validation.md',
    'docs/runbooks/production-readiness-checklist.md',
    'docs/runbooks/release-operations.md',
    'docs/runbooks/post-release.md',
    'docs/runbooks/deployment-manifest.md',
    'docs/runbooks/production-readiness-audit.md'
    'docs/architecture/research-job-queue.md'
    'scripts/finance-smoke-test.ps1'
)

foreach ($link in $requiredLinks) {
    if ($readme -notmatch [regex]::Escape($link)) {
        throw "README is missing link to $link"
    }
}

Write-Host 'Finance release-doc validation passed.'
