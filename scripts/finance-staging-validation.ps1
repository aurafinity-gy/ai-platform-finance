param(
    [Parameter(Mandatory = $true)]
    [string]$DatabaseUrl,
    [Parameter(Mandatory = $true)]
    [string]$ApiBaseUrl,
    [Parameter(Mandatory = $true)]
    [string]$BearerToken,
    [Parameter(Mandatory = $true)]
    [guid]$TenantId,
    [switch]$ApplyMigrations
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

if ($ApplyMigrations) {
    $migrationPaths = @(
        '202608130000_platform_audit_entries.sql',
        '202608130001_finance_research.sql',
        '202608310002_finance_research_jobs.sql',
        '202608310003_finance_research_worker_claim.sql'
    )
    foreach ($migration in $migrationPaths) {
        $path = Join-Path $repositoryRoot "infrastructure/supabase/migrations/$migration"
        & psql $DatabaseUrl -v ON_ERROR_STOP=1 -f $path
        if ($LASTEXITCODE -ne 0) {
            throw "Migration failed: $migration"
        }
    }
}

& pwsh -File (Join-Path $PSScriptRoot 'finance-smoke-test.ps1') -DatabaseUrl $DatabaseUrl
if ($LASTEXITCODE -ne 0) {
    throw 'Finance database smoke test failed.'
}

$headers = @{
    Authorization = "Bearer $BearerToken"
    'X-Tenant-Id' = $TenantId.ToString()
    'X-Correlation-Id' = "staging-$([guid]::NewGuid())"
    'Idempotency-Key' = "staging-$([guid]::NewGuid())"
}
$payload = @{
    contract_version = 1
    request_id = [guid]::NewGuid().ToString()
    source_domain = 'finance'
    source_reference = 'staging-validation'
    instrument = 'AAPL'
    objective = 'Validate asynchronous Finance research submission.'
    domain_context = @{ as_of = (Get-Date).ToUniversalTime().ToString('o') }
} | ConvertTo-Json -Depth 5

$response = Invoke-WebRequest `
    -Uri "$($ApiBaseUrl.TrimEnd('/'))/v1/finance-researches/jobs" `
    -Method Post `
    -Headers $headers `
    -ContentType 'application/json' `
    -Body $payload

if ($response.StatusCode -ne 202) {
    throw "Expected async Finance response 202, got $($response.StatusCode)."
}

$body = $response.Content | ConvertFrom-Json
if ($body.status -ne 'queued') {
    throw "Expected queued Finance job, got '$($body.status)'."
}

Write-Host "Finance staging validation passed for job $($body.job_id)."
