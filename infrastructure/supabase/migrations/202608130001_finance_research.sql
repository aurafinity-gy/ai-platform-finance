-- ADR-FIN003 Finance runtime persistence.
-- Owner: Finance. Classification: tenant-owned financial research data.
-- Prerequisite: Foundation platform.memberships, platform.audit_entries,
-- auth.jwt(), authenticated role, and platform_api role.
-- Forward fix: apply a later additive migration; do not drop shared data.

do $$
begin
    if to_regclass('platform.memberships') is null
       or to_regclass('platform.audit_entries') is null then
        raise exception 'Foundation platform schema must be initialized first';
    end if;
end
$$;

create schema if not exists finance;

create table finance.research_records (
    id uuid primary key,
    tenant_id uuid not null,
    actor_id uuid not null,
    request_id uuid not null,
    source_domain text not null check (
        source_domain ~ '^[a-z][a-z0-9.-]{0,63}$'
    ),
    source_reference text not null check (
        length(btrim(source_reference)) between 1 and 500
        and source_reference = btrim(source_reference)
    ),
    instrument text not null check (
        length(btrim(instrument)) between 1 and 20
        and instrument = btrim(instrument)
    ),
    recommendation text not null check (
        length(btrim(recommendation)) between 1 and 100
        and recommendation = btrim(recommendation)
    ),
    confidence double precision not null check (
        confidence >= 0 and confidence <= 1
    ),
    issues text[] not null default '{}',
    correlation_id text not null,
    created_at timestamptz not null,
    replayed boolean not null default false,
    status text not null check (status in ('accepted')),
    contract_version integer not null check (contract_version = 1),
    unique (tenant_id, source_domain, request_id)
);

create index finance_research_records_tenant_created_idx
    on finance.research_records (tenant_id, created_at, id);

create table finance.command_idempotency (
    tenant_id uuid not null,
    actor_id uuid not null,
    operation text not null check (operation = 'finance.research.create'),
    key_hash text not null check (length(key_hash) = 64),
    fingerprint text not null check (length(fingerprint) = 64),
    response_status integer not null check (response_status = 201),
    result jsonb not null check (jsonb_typeof(result) = 'object'),
    target_id uuid not null references finance.research_records(id),
    correlation_id text not null,
    created_at timestamptz not null,
    expires_at timestamptz not null,
    primary key (tenant_id, actor_id, operation, key_hash),
    check (expires_at > created_at)
);

alter table finance.research_records enable row level security;
alter table finance.research_records force row level security;
alter table finance.command_idempotency enable row level security;
alter table finance.command_idempotency force row level security;

revoke all on schema finance from public, anon, authenticated;
revoke all on all tables in schema finance from public, anon, authenticated;
grant usage on schema finance to authenticated;
grant insert on finance.research_records to authenticated;
grant select, insert on finance.command_idempotency to authenticated;

create policy finance_research_authorized_insert
on finance.research_records for insert to authenticated
with check (
    tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid
    and actor_id = auth.uid()
    and exists (
        select 1
        from platform.memberships membership
        where membership.tenant_id = finance_research_records.tenant_id
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

comment on table finance.research_records is
    'Finance-owned accepted research outputs for paper-trading workflows.';
comment on table finance.command_idempotency is
    '24-hour Finance research replay evidence; expired keys remain reserved.';
