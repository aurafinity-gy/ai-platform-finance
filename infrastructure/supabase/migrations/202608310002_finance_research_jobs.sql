-- ADR-FIN002 follow-up: durable Finance research jobs.
-- Owner: Finance. Classification: tenant-owned workflow payload.
-- Prerequisite: 202608130001_finance_research.sql.
-- Forward fix: apply additive migrations only.

create table finance.research_jobs (
    id uuid primary key,
    tenant_id uuid not null,
    actor_id uuid not null,
    request_id uuid not null,
    operation text not null check (operation = 'finance.research.create'),
    payload jsonb not null check (jsonb_typeof(payload) = 'object'),
    status text not null default 'queued' check (
        status in ('queued', 'processing', 'succeeded', 'failed')
    ),
    attempts integer not null default 0 check (attempts >= 0),
    available_at timestamptz not null default now(),
    locked_at timestamptz,
    locked_by text,
    last_error text,
    created_at timestamptz not null default now(),
    completed_at timestamptz,
    unique (tenant_id, request_id, operation)
);

create index finance_research_jobs_claim_idx
    on finance.research_jobs (status, available_at, created_at, id)
    where status = 'queued';

alter table finance.research_jobs enable row level security;
alter table finance.research_jobs force row level security;

grant insert, select on finance.research_jobs to authenticated;

create policy finance_research_jobs_actor_read
on finance.research_jobs for select to authenticated
using (
    tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid
    and actor_id = auth.uid()
);

create policy finance_research_jobs_authorized_insert
on finance.research_jobs for insert to authenticated
with check (
    tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid
    and actor_id = auth.uid()
    and exists (
        select 1
        from platform.memberships membership
        where membership.tenant_id = research_jobs.tenant_id
          and membership.actor_id = auth.uid()
          and membership.active
          and 'finance.research.create' = any(membership.permissions)
    )
);

comment on table finance.research_jobs is
    'Durable Finance research workflow jobs awaiting worker processing.';
