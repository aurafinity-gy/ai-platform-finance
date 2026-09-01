-- ADR-FIN002 follow-up: Finance worker queue claim policy.
-- Prerequisite: 202608310002_finance_research_jobs.sql.
-- Forward fix: apply additive migrations only.

grant select, update on finance.research_jobs to authenticated;

create policy finance_research_jobs_worker_claim
on finance.research_jobs for select to authenticated
using (
    tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid
    and exists (
        select 1
        from platform.memberships membership
        where membership.tenant_id = finance.research_jobs.tenant_id
          and membership.actor_id = auth.uid()
          and membership.active
          and 'finance.research.worker' = any(membership.permissions)
    )
);

create policy finance_research_jobs_worker_update
on finance.research_jobs for update to authenticated
using (
    tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid
    and exists (
        select 1
        from platform.memberships membership
        where membership.tenant_id = finance.research_jobs.tenant_id
          and membership.actor_id = auth.uid()
          and membership.active
          and 'finance.research.worker' = any(membership.permissions)
    )
)
with check (tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid);
