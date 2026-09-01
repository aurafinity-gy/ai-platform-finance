-- Forward fix for asynchronous Finance research result reads.
-- Owner: Finance. Classification: tenant-owned workflow output.

grant select on finance.research_records to authenticated;

create policy finance_research_actor_read
on finance.research_records for select to authenticated
using (
    tenant_id = nullif(auth.jwt() ->> 'tenant_id', '')::uuid
    and actor_id = auth.uid()
);
