param(
    [string]$DatabaseUrl = $env:FINANCE_DATABASE_URL
)

$requiredVariables = @(
    @{ Name = 'FINANCE_DATABASE_URL'; Value = $DatabaseUrl },
    @{ Name = 'FINANCE_AUTH_JWKS_URL'; Value = $env:FINANCE_AUTH_JWKS_URL },
    @{ Name = 'FINANCE_AUTH_ISSUER'; Value = $env:FINANCE_AUTH_ISSUER }
)

foreach ($variable in $requiredVariables) {
    if ([string]::IsNullOrWhiteSpace($variable.Value)) {
        throw "Missing required environment variable: $($variable.Name)"
    }
}

function Assert-TableExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TableName
    )

    $query = "select coalesce(to_regclass('$TableName')::text, 'absent')"
    $result = (& psql $DatabaseUrl -Atqc $query).Trim()
    if ($result -ne $TableName) {
        throw "Expected table $TableName but found '$result'"
    }
}

Assert-TableExists 'platform.memberships'
Assert-TableExists 'platform.audit_entries'
Assert-TableExists 'finance.research_records'
Assert-TableExists 'finance.command_idempotency'

Write-Host 'Finance smoke test passed.'

