-- Forward fix for the initial Finance RLS policy qualification.
-- The original migration created the tables before failing on policy creation.

drop policy if exists finance_research_authorized_insert
    on finance.research_records;
drop policy if exists finance_idempotency_actor_select
    on finance.command_idempotency;
drop policy if exists finance_idempotency_actor_insert
    on finance.command_idempotency;

create policy finance_research_authorized_insert
on finance.research_records for insert to authenticated
with check (
    tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid
    and actor_id = auth.uid()
    and exists (
        select 1
        from platform.memberships membership
        where membership.tenant_id = research_records.tenant_id
          and membership.actor_id = auth.uid()
          and membership.active
          and 'finance.research.create' = any(membership.permissions)
    )
);

create policy finance_idempotency_actor_select
on finance.command_idempotency for select to authenticated
using (
    tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid
    and actor_id = auth.uid()
);

create policy finance_idempotency_actor_insert
on finance.command_idempotency for insert to authenticated
with check (
    tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid
    and actor_id = auth.uid()
    and exists (
        select 1
        from platform.memberships membership
        where membership.tenant_id = command_idempotency.tenant_id
          and membership.actor_id = auth.uid()
          and membership.active
          and 'finance.research.create' = any(membership.permissions)
    )
);
