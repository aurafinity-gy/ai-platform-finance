#!/bin/sh
set -eu

db_container="${FINANCE_DB_CONTAINER:-ai-platform-foundation-database-1}"
tenant_id="${FINANCE_STAGING_TENANT_ID:-10000000-0000-0000-0000-000000000001}"
actor_id="${FINANCE_STAGING_ACTOR_ID:-20000000-0000-0000-0000-000000000001}"

docker exec "$db_container" psql -v ON_ERROR_STOP=1 -U supabase_admin -d postgres <<SQL
update platform.memberships
set permissions = array(
  select distinct permission
  from unnest(permissions || array['finance.research.create']::text[]) as permission
)
where tenant_id = '${tenant_id}'::uuid
  and actor_id = '${actor_id}'::uuid;

do $$
begin
  if not exists (
    select 1
    from platform.memberships
    where tenant_id = '${tenant_id}'::uuid
      and actor_id = '${actor_id}'::uuid
      and active
      and 'finance.research.create' = any(permissions)
  ) then
    raise exception 'Finance staging permission bootstrap verification failed';
  end if;
end
$$;
SQL

echo 'finance_staging_permissions.pass'
