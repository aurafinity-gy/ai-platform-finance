# Local Finance Migration Validation

This runbook applies the Finance additive migrations against a local Postgres
instance or shared development database. It uses synthetic identities and
non-production credentials only.

## Prerequisites

- The foundation/platform schema already exists in the target database.
- `platform.memberships` is present.
- You have permission to create `platform.audit_entries` and the Finance schema.
- You have a writable path to the target Postgres instance.
- The Finance workspace is synchronized with `uv sync --locked` if you want to
  run the repository tests after migration.

## Migration Order

Apply the platform audit table migration first, then the Finance research
migration:

1. `infrastructure/supabase/migrations/202608130000_platform_audit_entries.sql`
2. `infrastructure/supabase/migrations/202608130001_finance_research.sql`

That order matters because the Finance migration depends on the shared audit
table.

## Validate the Target Database

If you are using a local Postgres container, confirm the prerequisite tables
exist before applying anything:

```powershell
psql "$env:FINANCE_DATABASE_URL" -Atqc "select coalesce(to_regclass('platform.memberships')::text, 'absent'), coalesce(to_regclass('platform.audit_entries')::text, 'absent')"
```

Expected output:

```text
platform.memberships|absent
```

If `platform.memberships` is missing, initialize the platform schema before
applying the Finance migrations.

## Apply The Migrations

Use `psql` against the target database. Replace the connection string with the
database you want to update.

```powershell
psql "$env:FINANCE_DATABASE_URL" -v ON_ERROR_STOP=1 -f infrastructure/supabase/migrations/202608130000_platform_audit_entries.sql
psql "$env:FINANCE_DATABASE_URL" -v ON_ERROR_STOP=1 -f infrastructure/supabase/migrations/202608130001_finance_research.sql
```

If you are applying to a containerized database instead of a direct URL,
mount or copy the SQL files into the container and run the same commands
there.

## Verify The Result

Check that the Finance tables now exist:

```powershell
psql "$env:FINANCE_DATABASE_URL" -Atqc "select to_regclass('finance.research_records'), to_regclass('finance.command_idempotency')"
```

Expected output:

```text
finance.research_records|finance.command_idempotency
```

Also confirm that row level security is enabled:

```powershell
psql "$env:FINANCE_DATABASE_URL" -Atqc "select relname, relrowsecurity from pg_class join pg_namespace on pg_namespace.oid = pg_class.relnamespace where nspname = 'finance' and relname in ('research_records', 'command_idempotency') order by relname"
```

## Optional Local Capability Grant

For a synthetic test operator, grant the Finance research capability so the
runtime can authorize a request in a local environment:

```powershell
psql "$env:FINANCE_DATABASE_URL" -v ON_ERROR_STOP=1 -c "update platform.memberships set permissions = array_append(permissions, 'finance.research.create') where tenant_id = '10000000-0000-0000-0000-000000000001' and actor_id = '20000000-0000-0000-0000-000000000001' and not ('finance.research.create' = any(permissions));"
```

## Related Files

- [`docs/runbooks/finance-runtime-config.md`](finance-runtime-config.md)
- [`docs/decisions/0003-finance-runtime-uses-postgres-and-jwt-context.md`](../decisions/0003-finance-runtime-uses-postgres-and-jwt-context.md)
- [`infrastructure/supabase/migrations/202608130000_platform_audit_entries.sql`](../../infrastructure/supabase/migrations/202608130000_platform_audit_entries.sql)
- [`infrastructure/supabase/migrations/202608130001_finance_research.sql`](../../infrastructure/supabase/migrations/202608130001_finance_research.sql)
