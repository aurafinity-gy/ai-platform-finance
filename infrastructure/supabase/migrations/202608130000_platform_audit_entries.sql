-- Platform audit table used by Finance and other bounded contexts.
-- Owner: platform. Classification: append-only audit history.
-- Forward fix: apply additive migrations only.

create schema if not exists platform;

create table if not exists platform.audit_entries (
    id uuid primary key,
    tenant_id uuid not null,
    actor_id uuid not null,
    action text not null check (
        length(btrim(action)) between 1 and 200 and action = btrim(action)
    ),
    target_type text not null check (
        length(btrim(target_type)) between 1 and 100
        and target_type = btrim(target_type)
    ),
    target_id uuid not null,
    result text not null check (
        length(btrim(result)) between 1 and 100 and result = btrim(result)
    ),
    risk text not null check (
        length(btrim(risk)) between 1 and 100 and risk = btrim(risk)
    ),
    occurred_at timestamptz not null,
    metadata jsonb not null default '{}' check (jsonb_typeof(metadata) = 'object'),
    correlation_id text not null
);

create index if not exists platform_audit_entries_tenant_occurred_idx
    on platform.audit_entries (tenant_id, occurred_at, id);

alter table platform.audit_entries enable row level security;
alter table platform.audit_entries force row level security;

grant usage on schema platform to authenticated;
grant insert on platform.audit_entries to authenticated;

create policy platform_audit_authorized_insert
on platform.audit_entries for insert to authenticated
with check (
    tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid
    and actor_id = auth.uid()
);

comment on table platform.audit_entries is
    'Append-only platform audit records captured by Finance and other domains.';
